import wx

class RoomsWindow(wx.Frame):
    def __init__(self, parent):
        super(RoomsWindow, self).__init__(parent, title="Rooms")
        self.SetSize(wx.GetDisplaySize() - (100, 100))  # Adjust for a margin of 100 pixels
        self.CenterOnScreen()

        panel = wx.Panel(self)

        # Create a vertical box sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create pull-down menus for each room
        plants = ['Strawberry', 'Lettuce', 'Tomato', 'Swiss Chard']
        for i in range(4):
            room_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(panel, label=f"Room {i+1}:")
            room_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            choice = wx.Choice(panel, choices=plants)
            room_sizer.Add(choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            main_sizer.Add(room_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Add a "Send" button
        self.send_button = wx.Button(panel, label='Send')
        self.send_button.Bind(wx.EVT_BUTTON, self.OnSendButtonClick)
        main_sizer.Add(self.send_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 20)  # Increase bottom margin

        panel.SetSizer(main_sizer)

        self.Show(True)

    def OnSendButtonClick(self, event):
        # Print a message when the "Send" button is clicked
        wx.MessageBox("Send pressed", "Send Message", wx.OK | wx.ICON_INFORMATION)

class UserApplication(wx.Frame):
    def __init__(self, parent):
        super(UserApplication, self).__init__(parent, title="User Application", size=(400, 200))
        panel = wx.Panel(self)

        # Create a button to open the Rooms window
        open_rooms_button = wx.Button(panel, label='Open Rooms')
        open_rooms_button.Bind(wx.EVT_BUTTON, self.OnOpenRoomsButtonClick)

        # Add the button to the panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(open_rooms_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)

        self.Centre()
        self.Show(True)

    def OnOpenRoomsButtonClick(self, event):
        # Open the Rooms window
        rooms_window = RoomsWindow(self)

def main():
    app = wx.App()
    UserApplication(None)
    app.MainLoop()

if __name__ == '__main__':
    main()
