import npyscreen
import pyperclip

import createVm
import main
import popup
import selectableGrid
import virtualMachine

class SnapshotGrid(selectableGrid.SelectableGrid):
    def __init__(self, screen, *args, **keywords):
        super().__init__(screen, *args, **keywords)
        self.form.start_polling(self.refresh, self)
        self.refresh()
        self.col_titles = ["ID", "Description", "Size (Gb)", "Volume"]

        def on_selection(line):
            popup.editSnapshot(self.form, line)

        self.on_selection = on_selection

    def refresh(self):
        groups = main.GATEWAY.ReadSnapshots()['Snapshots']
        values = list()
        for g in groups:
            values.append([g['SnapshotId'], g['Description'], g['VolumeSize'], g['VolumeId']])
        self.values = values
