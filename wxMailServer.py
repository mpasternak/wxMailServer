# -*- encoding: utf-8 -*-
import smtpd
import webbrowser
import asyncore
import threading
import Queue
from wx import html
import re

import wx
from wx._core import EVT_ACTIVATE
import wx.lib.newevent


TRAY_TOOLTIP = 'wxMailServer'
TRAY_ICON = 'icon.png'
messages = Queue.Queue()



def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item

class MyHtmlWindow(html.HtmlWindow):
    def __init__(self, parent, id):
        html.HtmlWindow.__init__(self, parent, id, style=wx.NO_FULL_REPAINT_ON_RESIZE)

    def OnLinkClicked(self, linkinfo):
        webbrowser.open(linkinfo.GetHref())


class Example(wx.Dialog):

    def __init__(self, peer, mailfrom, rcpttos, data, *args, **kw):
        super(Example, self).__init__(*args, **kw)
        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(TRAY_ICON)))
        pnl = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        st1 = wx.StaticText(pnl, label='From')
        st2 = wx.StaticText(pnl, label='To ')
        st3 = wx.StaticText(pnl, label='Subject')

        self.tc1 = wx.TextCtrl(pnl, size=(360, -1))
        self.tc1.SetValue(mailfrom)
        self.tc2 = wx.TextCtrl(pnl, size=(360, -1))
        self.tc2.SetValue(unicode(rcpttos))
        self.tc3 = wx.TextCtrl(pnl, size=(460, -1))

        self.tc = MyHtmlWindow(pnl, -1)

        import email
        msg = email.message_from_string(data)

        buf = "<body>"
        buf += "<table>"
        for key, value in msg._headers:
            if key == 'Subject':
                self.tc3.SetValue(value)
            buf += "<tr><td align=right><b>%s:</b></td><td>%s</td></tr>" % (key, value)
        buf += "</table>"

        re_match_urls = re.compile(r"""((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.‌​][a-z]{2,4}/)(?:[^\s()<>]+|(([^\s()<>]+|(([^\s()<>]+)))*))+(?:(([^\s()<>]+|(‌​([^\s()<>]+)))*)|[^\s`!()[]{};:'".,<>?«»“”‘’""``'']))""", re.DOTALL)

        data = re_match_urls.sub(lambda x: '<a href="%(url)s">%(url)s</a>' % dict(url=str(x.group())), msg._payload)
        buf += "<pre>" + unicode(data, "utf-8") + "</pre>"
        buf += "</body>"

        self.tc.SetPage(buf)

        button_send = wx.Button(pnl, label='Thanks, Doge!')

        hbox1.Add(st1, flag=wx.LEFT, border=10)
        hbox1.Add(self.tc1, flag=wx.LEFT, border=35)
        hbox2.Add(st2, flag=wx.LEFT, border=10)
        hbox2.Add(self.tc2, flag=wx.LEFT, border=50)
        hbox3.Add(st3, flag=wx.LEFT, border=10)
        hbox3.Add(self.tc3, flag=wx.LEFT, border=20)
        vbox.Add(hbox1, flag=wx.TOP, border=10)
        vbox.Add(hbox2, flag=wx.TOP, border=10)
        vbox.Add(hbox3, flag=wx.TOP, border=10)
        vbox.Add(self.tc, proportion=1, flag=wx.EXPAND | wx.TOP |
            wx.RIGHT | wx.LEFT, border=15)
        vbox.Add(button_send, flag=wx.ALIGN_CENTER | wx.TOP |
            wx.BOTTOM, border=20)

        button_send.Bind(EVT_ACTIVATE, self.Close)
        pnl.SetSizer(vbox)

        self.SetSize((960, 820))
        self.SetTitle('wxMailServer received a message')
        self.Centre()
        self.ShowModal()
        self.Destroy()

class DebuggingServer(smtpd.SMTPServer):
    # Do something with the gathered message
    def process_message(self, peer, mailfrom, rcpttos, data):
        messages.put([peer, mailfrom, rcpttos, data])


def loop():
    while 1:
        asyncore.poll(timeout=.01)

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self):
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        #create_menu_item(menu, 'Say Hello', self.on_hello)
        #menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        pass

    def on_hello(self, event):
        pass

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)


def OnPoll(x):
    if not messages.empty():
        msg = messages.get()
        peer, frm, rcptto, data = msg
        Example(peer, frm, rcptto, data, None)


def main():
    app = wx.PySimpleApp()
    TaskBarIcon()


    DebuggingServer(
        ('localhost', 25),
        ('localhost', 25))

    t = threading.Thread(target=loop)
    t.setDaemon(1)
    t.start()

    poller = wx.Timer(None, wx.NewId())
    app.Bind(wx.EVT_TIMER, OnPoll)
    poller.Start(20, wx.TIMER_CONTINUOUS)

    app.MainLoop()


if __name__ == '__main__':
    main()