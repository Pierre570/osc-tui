import threading
import curses
import time

import npyscreen
import pyperclip

import createVm
import createVolume
import createSnapshot
import instancesGrid
import snapshotGrid
import main
import popup
import securityGroupsGrid
import securityRulesGrid
import selectableGrid
import virtualMachine
import volumesGrid

MODE = "INSTANCES"
SELECTED_BUTTON = 0
CURRENT_GRID_CLASS = instancesGrid.InstancesGrid


POLLING = False

class my_thread(threading.Thread):
    def __init__(self, to_run, ctx):
        threading.Thread.__init__(self)
        self.to_run = to_run
        self.stop = False
        self.stopped = False
        self.ctx = ctx
    def stop(self):
        self.stop = True
    def run(self):
        self.to_run()
        self.stopped = True

class mainMenu(npyscreen.MultiLineAction):
    def __init__(self, screen, vmform=None, draw_line_at=6, *args, **keywords):
        super().__init__(screen, *args, **keywords)
        self.vmform = vmform
        self.cursor_line = SELECTED_BUTTON
        self.scroll_exit = True
        self.draw_line_at = draw_line_at

    def actionHighlighted(self, act_on_this, key_press):
        if key_press == 10:

            if self.vmform:
                global MODE
                if MODE == 'INSTANCES':
                    if act_on_this == "CREATE NEW":
                        self.vmform.parentApp.addForm("CREATE_VM",
                                                      createVm.CreateVm,
                                                      name="osc-tui")
                        self.vmform.parentApp.switchForm("CREATE_VM")
                        return
                elif MODE == 'SECURITY':
                    if act_on_this == "CREATE NEW":
                        popup.newSecurityGroup(self.vmform)
                        return
                elif MODE == 'SECURITY-VM':
                    if act_on_this == "ADD SEC-GROUP":
                        popup.addSecurityGroupToVm(self.vmform)
                        return
                elif MODE == 'SECURITY-RULES':
                    if act_on_this == "CREATE NEW":
                        popup.newSecurityGroupRule(self.vmform)
                        return
                    elif act_on_this == 'ADD SSH MY IP':
                        main.GATEWAY.CreateSecurityGroupRule(
                            FromPortRange=22,
                            IpProtocol="tcp",
                            IpRange=main.IP + "/32",
                            ToPortRange=22, SecurityGroupId=main.SECURITY_GROUP,
                            Flow="Inbound",
                        )
                        self.vmform.current_grid.refresh()
                        self.vmform.current_grid.display()
                        return
                elif MODE == 'VOLUMES':
                    if act_on_this == 'CREATE NEW':
                        self.vmform.parentApp.addForm("CREATE_VOLUME",
                                                      createVolume.CreateVolume,
                                                      name="osc-tui")
                        self.vmform.parentApp.switchForm("CREATE_VOLUME")
                        return
                elif MODE == 'SNAPSHOT':
                    if act_on_this == 'CREATE NEW':
                        self.vmform.parentApp.addForm("CREATE_SNAPSHOT",
                                                      createSnapshot.CreateSnapshot,
                                                      name="osc-tui")
                        self.vmform.parentApp.switchForm("CREATE_SNAPSHOT")
                        return
                if act_on_this == "EXIT":
                    main.kill_threads()
                    self.vmform.parentApp.switchForm("MAIN")
                    return
                elif act_on_this == "REFRESH":
                    if hasattr(self.vmform, 'current_grid'):
                        self.vmform.current_grid.refresh()
                        self.vmform.current_grid.display()
                    return
                MODE = act_on_this
                global SELECTED_BUTTON
                if act_on_this == 'INSTANCES' or act_on_this == 'SECURITY':
                    SELECTED_BUTTON = 7
                else:
                    SELECTED_BUTTON = self.cursor_line
                self.vmform.reload()


    def set_up_handlers(self):
        super().set_up_handlers()
        self.add_handlers({curses.KEY_RIGHT: self.h_exit_down})
        self.add_handlers({curses.KEY_LEFT: self.h_exit_up})

    def h_cursor_line_up(self, input):
        super().h_cursor_line_up(input)
        if(self.draw_line_at == self.cursor_line):
            super().h_cursor_line_up(input)
        if(self.draw_line_at == self.cursor_line):
            super().h_cursor_line_down(input)

    def h_cursor_line_down(self, input):
        super().h_cursor_line_down(input)
        if(self.draw_line_at == self.cursor_line):
            super().h_cursor_line_down(input)
        if(self.draw_line_at == self.cursor_line):
            super().h_cursor_line_up(input)


class MainForm(npyscreen.FormBaseNew):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)

    def create(self):
        def build_line(size):
            out = ''
            for i in range(0, size):
                out = out + '─'
            return out
        menu_desc = (
            "INSTANCES SECURITY VOLUMES SNAPSHOT REFRESH EXIT " +
            build_line(15)).split()
        global CURRENT_GRID_CLASS
        y, _ = self.useable_space()
        self.rowOffset = 16
        if MODE == "INSTANCES":
            CURRENT_GRID_CLASS = instancesGrid.InstancesGrid
            menu_desc.append('CREATE NEW')
        elif MODE == "SECURITY":
            CURRENT_GRID_CLASS = securityGroupsGrid.SecurityGroupsGrid
            menu_desc.append('CREATE NEW')
        elif MODE == "SECURITY-VM":
            menu_desc.append('ADD SEC-GROUP')
        elif MODE == 'SECURITY-RULES':
            CURRENT_GRID_CLASS = securityRulesGrid.SecurityRulesGrid
            menu_desc.append('CREATE NEW')
            menu_desc.append('ADD SSH MY IP')
        elif MODE == 'VOLUMES':
            CURRENT_GRID_CLASS = volumesGrid.VolumeGrid
            menu_desc.append('CREATE NEW')
        elif MODE == 'VOLUMES-EDIT':
            CURRENT_GRID_CLASS = volumesGrid.VolumeGridEdit
        elif MODE == 'VOLUMES-VM':
            CURRENT_GRID_CLASS = volumesGrid.VolumeGridForOneInstance
        elif MODE == 'SNAPSHOT':
            CURRENT_GRID_CLASS = snapshotGrid.SnapshotGrid
            menu_desc.append('CREATE NEW')
        self.add_widget(
            mainMenu,
            vmform=self,
            relx=1,
            max_width=14,
            values=menu_desc,
        )
        y, _ = self.useable_space()

        self.current_grid = self.add(
            CURRENT_GRID_CLASS,
            form=self,
            name="Instances",
            value=0,
            additional_y_offset=2,
            additional_x_offset=2,
            column_width=21,
            select_whole_line=True,
            scroll_exit=True,
            relx=17,
            rely=2,
        )

    def on_screen(self):
        super().on_screen()

    def draw_form(self, ):
        _, MAXX = self.curses_pad.getmaxyx()
        super().draw_form()
        MAXX, _ = self.curses_pad.getmaxyx()
        self.curses_pad.vline(1, 15, curses.ACS_VLINE, MAXX - 2)

    def reload(self):
        main.kill_threads()
        self.parentApp.addForm("Cockpit", MainForm, name="osc-tui")
        self.parentApp.switchForm("Cockpit")




    def thread(self, fct, ctx):
        t = my_thread(fct, ctx)
        t.start()
        main.add_thread(t)
        return t

    def start_polling(self, fct, ctx):
        th = self.thread(fct, ctx)
        i = 0
        stri = "Polling"
        while th.stopped == False:
            if(i > 3):
                i = 0
            for n in range(0, i):
                stri += "."
            i = i + 1
            x = int(curses.COLS/2 - len(stri)/2)
            y = curses.LINES
            x = 5
            y = 5
            self.curses_pad.addstr(y, x, stri)
            time.sleep(1)

