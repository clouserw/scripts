# Passive aggressively auto-replies to private messages which say only the word
# 'ping' thus escalating the unwinnable war of people pinging without saying anything
# else.
#
# Author: Wil Clouser <clouserw@micropipes.com>

SCRIPT_NAME    = "autopong"
SCRIPT_AUTHOR  = "Wil Clouser <clouserw@micropipes.com>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC    = "Auto-replies to 'ping' queries"

import_ok = True

try:
   import weechat as w
except:
   print "Script must be run under weechat. http://www.weechat.org"
   import_ok = False

def privmsg(data, buffer, date, tags, displayed, is_hilight, prefix, msg):

  if w.buffer_get_string(buffer, "localvar_type") == "private":
     if msg == "ping":
         w.command(buffer, "pong")
  return w.WEECHAT_RC_OK

if __name__ == "__main__" and import_ok:

   if w.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                 SCRIPT_DESC, "", ""):
      w.hook_print("", "", "", 1, "privmsg", "")
