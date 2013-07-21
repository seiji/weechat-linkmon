import weechat
import re
import time

SCRIPT_NAME    = "urlhanger"
SCRIPT_AUTHOR  = "Seiji Toyama"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL"
SCRIPT_DESC    = "Url hangar"
CONFIG_FILE_NAME= "urlhangar"
SCRIPT_COMMAND = "urlh"

octet = r'(?:2(?:[0-4]\d|5[0-5])|1\d\d|\d{1,2})'
ipAddr = r'%s(?:\.%s){3}' % (octet, octet)
# Base domain regex off RFC 1034 and 1738
label = r'[0-9a-z][-0-9a-z]*[0-9a-z]?'
domain = r'%s(?:\.%s)*\.[a-z][-0-9a-z]*[a-z]?' % (label, label)
urlRe = re.compile(r'(\w+://(?:%s|%s)(?::\d+)?(?:/[^\]>\s]*)?)' % (domain, ipAddr), re.I)

class URLBuffer:
    def __init__(self):
        self.url_infos = {}
        self.urls = []
        self.current_line = 0
        self.max_url_size = 100
        self.max_buffer_width = 0

        url_buffer = weechat.buffer_new("#url_hangar", "buffer_input_cb",  "", "buffer_close_cb", "")
        weechat.buffer_set(url_buffer, "type", "free")
        weechat.buffer_set(url_buffer, "key_bind_ctrl-R",        "/urlh **refresh")
        weechat.buffer_set(url_buffer, "key_bind_meta2-A",       "/urlh **up")
        weechat.buffer_set(url_buffer, "key_bind_meta2-B",       "/urlh **down")
        weechat.buffer_set(url_buffer, "key_bind_meta-ctrl-J",   "/urlh **enter")
        weechat.buffer_set(url_buffer, "key_bind_meta-ctrl-M",   "/urlh **enter")
        weechat.buffer_set(url_buffer, "key_bind_meta-ctrl-P",   "/urlh **up")
        weechat.buffer_set(url_buffer, "key_bind_meta-ctrl-N",   "/urlh **down")
        weechat.buffer_set(url_buffer, "key_bind_meta-meta2-1./~", "/urlh **scroll_top")
        weechat.buffer_set(url_buffer, "key_bind_meta-meta2-4~", "/urlh **scroll_bottom")
        weechat.buffer_set(url_buffer, "title","Lists the urls in the applications")
        weechat.buffer_set(url_buffer, "display", "1")
        self.url_buffer = url_buffer

    def add_url(self, bufferp, url, tags, message):
        buffer_name = weechat.buffer_get_string(bufferp, "short_name"),
        info = message
        info = info.replace(url, '')

        match = re.search('(^|,)nick_([^,]*)(,|$)', tags)
        nick = match.group(2)
        
        # if notice
        info = info.replace("Notice(" + nick + "):", '')
        self.url_infos[url] =  {
            "url": url,
            "buffer": buffer_name[0],
            "time": time.strftime("%H:%M:%S"),
            "info": info
        }

        if url in self.urls:
            self.urls.remove(url)
        self.urls.insert(0,url)
        while len(self.urls) > self.max_url_size:
            self.urls.pop()

    def key_event(self, data, bufferp, args):
        if args == 'up':
            if self.current_line > 0:
                self.current_line = self.current_line -1
                self.refresh_line (self.current_line + 1)
                self.refresh_line (self.current_line)
                self.scroll_buffer()

        elif args == 'down':
            if self.current_line < len(self.urls) - 1:
                self.current_line = self.current_line +1
                self.refresh_line (self.current_line - 1)
                self.refresh_line (self.current_line)
                self.scroll_buffer

        elif args == "scroll_top":
            temp_current = self.current_line
            self.current_line =  0
            self.refresh_line (temp_current)
            self.refresh_line (self.current_line)
            weechat.command(self.url_buffer, "/window scroll_top")
            pass
        elif args == "scroll_bottom":
            temp_current = self.current_line
            self.current_line =  len(self.urls)
            self.refresh_line (temp_current)
            self.refresh_line (self.current_line)
            weechat.command(self.url_buffer, "/window scroll_bottom")
        elif args == "enter":
            url = self.urls[self.current_line]
            weechat.prnt("", "keyevent:" + args)
            if url:
                weechat.hook_process("~/bin/open_url.scpt '%s'" % url ,60000, "", "")
            
        return weechat.WEECHAT_RC_OK

    def scroll_buffer(self):
        infolist = weechat.infolist_get("window", "", "current")
        if (weechat.infolist_next(infolist)):
            start_line_y = weechat.infolist_integer(infolist, "start_line_y")
            chat_height = weechat.infolist_integer(infolist, "chat_height")
            if(start_line_y > self.current_line):
                weechat.command(self.url_buffer, "/window scroll -%i" %(start_line_y - self.current_line))
            elif(start_line_y <= self.current_line - chat_height):
                weechat.command(self.url_buffer, "/window scroll +%i"%(self.current_line - start_line_y - chat_height + 1))
        weechat.infolist_free(infolist)

    def refresh(self):
        y = 0
        for x in self.urls:
            self.refresh_line (y)
            y += 1

    def refresh_line(self, y):
        format = "%%s%%s %%s%%-%ds%%s%%s" % (self.max_buffer_width+4)
        color_time = "cyan"
        color_buffer = "red"
        color_url = "blue"
        color_bg_selected = "black"
        if y == self.current_line:
            color_time = "%s,%s" % (color_time, color_bg_selected)
            color_buffer = "%s,%s" % (color_buffer, color_bg_selected)
            color_url = "%s,%s" % (color_url, "")

        color_time = weechat.color(color_time)
        color_buffer = weechat.color(color_buffer)
        color_url = weechat.color(color_url)

        url = self.urls[y]
        url_info = self.url_infos[url]
        text = format % (color_time,
                    url_info['time'],
                    color_buffer,
                    url_info['buffer'],
                    color_url,
                    url_info['info']
                         )
        weechat.prnt_y(self.url_buffer,y,text)

    def set_max_buffer_width(self, bufferp):
        if self.max_buffer_width < len(bufferp):
            self.max_buffer_width = len(bufferp)

        
def buffer_input_cb(data, buffer, input_data):
    return weechat.WEECHAT_RC_OK

def buffer_close_cb(data, buffer):
    return weechat.WEECHAT_RC_OK
    
def url_check_cb(data, bufferp, uber_empty, tagsn, isdisplayed, ishilight, prefix, message):
    if not message:
        return
    if message.startswith("[urlhangar]"):
        return

    global url_buffer
    for url in urlRe.findall(message):
        url_buffer.add_url(bufferp, url, tagsn, message)

    url_buffer.set_max_buffer_width(bufferp)
    url_buffer.refresh()

    return weechat.WEECHAT_RC_OK
    
def unload_cb():
    """ Function called when script is unloaded. """
    return weechat.WEECHAT_RC_OK

def command_cb(data, bufferp, args):
    global url_buffer
    if args[0:2] == "**":
        url_buffer.key_event(data, bufferp, args[2:])
        return weechat.WEECHAT_RC_OK
    return weechat.WEECHAT_RC_OK
    
if (weechat.register(
        SCRIPT_NAME,
        SCRIPT_AUTHOR,
        SCRIPT_VERSION,
        SCRIPT_LICENSE,
        SCRIPT_DESC,
        "unload_cb",
        "")):
    weechat.prnt("", "Hello, from python script!")
    url_buffer = URLBuffer()

    weechat.hook_print("", "", "", 1, "url_check_cb", "")
    weechat.hook_command(SCRIPT_COMMAND,
                         "url hangar",
                         "command sample",
                         "description of arguments...",
                         "list",
                         "command_cb", "")

