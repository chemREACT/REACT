
from PyQt5.QtWidgets import QMainWindow, QMenu, QTableWidgetItem, QApplication
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QColor
from UIs.AnyPlot import Ui_AnyPlotter
from mods.ReactPlot import PlotEnergyDiagram
from mods.common_functions import random_color, select_color, is_number


class Plotter(QMainWindow, Ui_AnyPlotter):
    def __init__(self, parent):
        super(Plotter, self).__init__(parent)
        # find better alternative to , Qt.WindowStaysOnTopHint

        # Matplotlib.pyplot window:
        self.plot = None

        self.ui = Ui_AnyPlotter()
        self.ui.setupUi(self)

        #Fix right-clickable menu:
        self.ui.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.table_menu)


        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowTitle("REACT - AnyPlot")

        self.ui.tableWidget.cellDoubleClicked.connect(self.double_click_color)
        self.ui.button_plot.clicked.connect(self.make_plot)
        self.ui.button_set_rows_columns.clicked.connect(self.update_table)

        self.ui.checkBox_style.clicked.connect(self.update_plot)
        self.ui.tableWidget.itemChanged.connect(self.update_plot)

        # Clipboard for copy/paste functionality
        self.clipboard = QApplication.clipboard()

        # Set a random color for the first column
        self.set_colour(0, random_color())
        self.set_title(0, "Title")

        self.numerate_vertical_headers()

        # TODO check if user is using OS:
        self.remove_mac_spinbox_focus()

    def remove_mac_spinbox_focus(self):
        """
        Removes the rather annoying blue focus border that is default on MAC os
        :return:
        """
        spins = [self.ui.spinBox_legend_size, self.ui.spinBox_rows, self.ui.spinBox_ticklabel_size,
                 self.ui.spinBox_axis_fontsize, self.ui.spinBox_columns]
        for spin in spins:
            spin.setAttribute(Qt.WA_MacShowFocusRect, False)

    def update_plot(self):
        if self.plot:
            self.make_plot()

    def numerate_vertical_headers(self):
        """
        Make vertical headers start from 1..N
        :return:
        """
        for i in range(2, self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(str(i-1)))

    def table_menu(self, event):
        """
        Opens up menu when tableWidget is right-clicked
        :param position:
        :return:
        """
        # If not cells are selected, return
        if not self.ui.tableWidget.selectedRanges():
            return

        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")

        action = menu.exec_(self.ui.tableWidget.mapToGlobal(event))

        if action is copy_action:
            self.copy_to_clipboard()
        if action is paste_action:
            self.paste_from_clipboard()

    def paste_from_clipboard(self):
        """
        Paste from clipboard to tablewidget.
        :return:
        """
        row_start = self.ui.tableWidget.selectedIndexes()[0].row()
        # Can not allow pasting on color row (row = 0)
        if row_start == 0:
            row_start = 1

        column_start = self.ui.tableWidget.selectedIndexes()[0].column()
        row_text = self.clipboard.text().split("\n")

        for row in range(len(row_text)):
            row_index = row_start + row
            # Check if there are enough rows
            if (self.ui.tableWidget.rowCount() - 2) < (row_index + 1):
                self.add_rows(self.ui.tableWidget.rowCount(), row_index - 1)

            column_text = row_text[row].split("\t")
            for column in range(len(column_text)):
                column_index = column_start + column
                # Check if there are enough columns:
                if self.ui.tableWidget.columnCount() < (column_index + 1):
                    self.add_columns(self.ui.tableWidget.columnCount(), column_index + 1)
                item = QTableWidgetItem(column_text[column].strip("\t").strip("\n"))
                self.ui.tableWidget.setItem(row_index, column_index, item)

    def copy_to_clipboard(self):
        """
        Copies text from selected cells to clipboard.
        :return:
        """

        text_ = ""
        row = None
        for index in self.ui.tableWidget.selectedIndexes():
            if not row:
                row = index.row()

            elif index.row() != row:
                text_ += "\n"
                row = index.row()
            else:
                text_ += "\t"

            try:
                text_ += self.ui.tableWidget.item(index.row(), index.column()).text().strip("\n")
            except AttributeError:
                text_ += ""

        self.clipboard.setText(text_)

    def update_table(self):
        """
        :return:
        """
        # -2 because the 2 first entries are reserved for color and title
        rows_old = int(self.ui.tableWidget.rowCount() - 2)
        rows_new = int(self.ui.spinBox_rows.value())

        columns_old = int(self.ui.tableWidget.columnCount())
        columns_new = int(self.ui.spinBox_columns.value())

        # Add or delete rows?
        if rows_new > rows_old:
            self.add_rows(rows_old+2, rows_new)
        elif rows_new < rows_old:
            self.delete_rows(rows_old+2, rows_new)
        else:
            pass

        # Add or delete columns?
        if columns_new > columns_old:
            self.add_columns(columns_old, columns_new)
        elif columns_new < columns_old:
            self.delete_columns(columns_old, columns_new)
        else:
            pass

    def add_columns(self, insert_index, columns_total):
        """
        :param insert_index:
        :param columns_total:
        :return:
        """
        while int(self.ui.tableWidget.columnCount()) < columns_total:
            self.ui.tableWidget.insertColumn(insert_index)
            self.set_colour(insert_index, random_color())
            self.set_title(insert_index, "Title")
            insert_index += 1

    def delete_columns(self, delete_index, columns_total):
        """
        :param delete_index:
        :param columns_total:
        :return:
        """
        while int(self.ui.tableWidget.columnCount()) > columns_total:
            self.ui.tableWidget.removeColumn(delete_index)
            delete_index -= 1

    def add_rows(self, insert_index, rows_total):
        """
        :param insert_index: Where to insert new row(s)
        :param rows_total: Final number of rows in table
        """
        while int(self.ui.tableWidget.rowCount() - 2) < rows_total:
            self.ui.tableWidget.insertRow(insert_index)
            insert_index += 1

        self.numerate_vertical_headers()

    def delete_rows(self, delete_index, rows_total):
        """
        :param delete_index: Index to delete
        :param rows_total: Final number of rows in table
        """

        while int(self.ui.tableWidget.rowCount() - 2) > rows_total:
            self.ui.tableWidget.removeRow(delete_index)
            delete_index -= 1

    def double_click_color(self):
        """
        If color row is double-clicked, open color selector, and color row.
        :return:
        """
        # row column
        row = self.ui.tableWidget.currentRow()
        if row != 0:
            return None

        column = self.ui.tableWidget.currentColumn()
        color = select_color(parent=self)

        self.set_colour(column, color)

    def set_colour(self, column=None, color=None):
        """
        Sets color of row=0 for column.
        :return:
        """
        row = 0

        # color name in hex:
        self.ui.tableWidget.setItem(row, column, QTableWidgetItem())
        self.ui.tableWidget.item(row, column).setBackground(QColor(color))

    def set_title(self, column=0, title="Title"):
        """
        Set title for plot in column
        :param column:
        :param title:
        """
        self.ui.tableWidget.setItem(1, column, QTableWidgetItem(title))

    def make_plot(self):
        """
        TODO this funciton needs to check content of cells - could be NoneType or Text
        :return:
        """
        colors = list()
        titles = list()
        plots = list()
        for column in range(self.ui.tableWidget.columnCount()):
            energies = list()
            for row in range(self.ui.tableWidget.rowCount()):
                if row == 0:
                    color = self.ui.tableWidget.item(row, column).background().color().name()
                    colors.append(color)
                elif row == 1:
                    try:
                        titles.append(self.ui.tableWidget.item(row, column).text())
                    except AttributeError:
                        titles.append("Title%d" % row)
                else:
                    try:
                        value = self.ui.tableWidget.item(row, column).text()
                    except AttributeError:
                        value = None

                    if is_number(value):
                        energies.append(float(value))
                    else:
                        energies.append(None)
            plots.append(energies)

        react_style = self.ui.checkBox_style.isChecked()
        y_title = self.ui.lineEdit_ytitle.text()
        x_title = self.ui.lineEdit_xtitle.text()

        if self.ui.checkBox_customnames.isChecked():
            custom_names = self.ui.lineEdit_customnames.text().split(",")
        else:
            custom_names = None

        if self.ui.checkBox_activation.isChecked():
            activation = True
        else:
            activation = False
        
        if self.ui.checkBox_reaction.isChecked():
            reaction = True
        else:
            reaction = False

        if not self.plot:
            self.plot = PlotEnergyDiagram(ene_array=plots, parent=self, legends=titles, line_colors=colors,
                                          y_title=y_title, x_title=x_title, plot_legend=True, react_style=react_style, custom_names=custom_names,
                                          activation=activation, reaction=reaction)
            self.read_plot_settings()

            self.plot.plot_energy_diagram()


        else:
            self.read_plot_settings()
            self.plot.update_plot(ene_array=plots, legends=titles, line_colors=colors, y_title=y_title, x_title=x_title,
                                  plot_legend=True, react_style=react_style)

    def read_plot_settings(self):
        """

        :return:
        """
        settings = {self.plot.set_axes_label_size: self.ui.spinBox_axis_fontsize,
                    self.plot.set_xtick_label_size: self.ui.spinBox_ticklabel_size,
                    self.plot.set_ytick_label_size: self.ui.spinBox_ticklabel_size,
                    self.plot.set_legend_size: self.ui.spinBox_legend_size}

        for setter in settings.keys():
            setter(settings[setter].value())

    def closeEvent(self, event):
        """
        Close matplotlib if open
        :param event:
        """
        if self.plot:
            self.plot.close(event)

