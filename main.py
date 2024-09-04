# TODO:
# threading? https://www.geeksforgeeks.org/writing-files-background-python/
# Symbol 없는 경우 error handling
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
from pyqt.stock import UsStock
from pyqt.stock import Crypto
from pyqt.stock import KorStock
from pyqt.util import resource_path


class Window(QWidget):

    def __init__(self):
        super().__init__()
        self.read_data()
        self.init_ui()

    def read_data(self):
        self.data_path = resource_path('data/watchlist.csv')
        self.data = pd.read_csv(self.data_path, dtype=str)
        self.data[['Name', 'Crypto']] = self.data[['Name', 'Crypto']].fillna('')

    def init_ui(self):
        self.setWindowTitle('Stock Chart') 
        self.resize(800, 1000)
        
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.stock_tab(), 'Stock Chart')
        self.tabs.addTab(self.watchlist(), 'Watchlist')
        layout.addWidget(self.tabs)

    def stock_tab(self):
        outer_most = QWidget()

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)

        stock_chart_tab = QWidget()
        stock_chart_tab.setLayout(self.layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(stock_chart_tab)
        
        content = QHBoxLayout()
        content.addWidget(self.scroll)
        outer_most.setLayout(content)
        return outer_most

    def watchlist(self):
        watchlist_tab = QWidget()
        layout = QVBoxLayout()
        layout.addLayout(self.add_form())

        self.table = QTableView(self)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.match_selection = []
        self.table.clicked.connect(self.clear_selection)
        self.col_len = len(self.data.columns)
        self.content = QStandardItemModel(0, self.col_len, self)
        self.content.setHorizontalHeaderLabels(self.data.columns)
        self.table.setModel(self.content)

        layout.addWidget(self.table)
        self.read_watchlist()

        remove_button = QPushButton('Remove Selected Stock', self)
        remove_button.setFixedWidth(200)
        remove_button.setShortcut('Backspace')
        remove_button.clicked.connect(self.remove_item)
        layout.addWidget(remove_button)

        watchlist_tab.setLayout(layout)
        return watchlist_tab

    def clear_selection(self, item):
            self.match_selection.append(item.row())

            if len(self.match_selection) == 2:
                if self.match_selection[0] == self.match_selection[1]:
                    self.table.clearSelection()
                    self.match_selection = []
                else:
                    self.match_selection.pop(0)        

    def draw_label(self, label_name):
        label = QLabel(label_name, self)
        input_box = QLineEdit(self)
        input_box.setFixedWidth(150)
        return label, input_box

    def add_form(self):
        form_layout = QVBoxLayout()

        symbol_label, self.stock = self.draw_label('Symbol')
        form_layout.addWidget(symbol_label)
        form_layout.addWidget(self.stock)

        company_label, self.company = self.draw_label('Name')
        form_layout.addWidget(company_label)
        form_layout.addWidget(self.company)

        self.check_box = QCheckBox('Crypto', self)
        form_layout.addWidget(self.check_box)

        add_button = QPushButton('Add', self)
        add_button.setFixedWidth(100)
        add_button.setShortcut('Return')
        add_button.clicked.connect(self.add_item)
        form_layout.addWidget(add_button)
        return form_layout

    def group(self, symbol, stock_name, is_crypto: bool=False, is_kor: bool=False):
        group_box = QGroupBox()
        group_box.setFixedHeight(300)

        layout = QVBoxLayout()
        name_layout = QHBoxLayout()
        name = QLabel(stock_name)
        name.setFont(QFont('Arial', 18, weight=QFont.Bold))
        ticker = QLabel(f'({symbol})')
        name_layout.addWidget(name)
        name_layout.addWidget(ticker)
        name_layout.addStretch()
        layout.addLayout(name_layout)
        
        if not is_kor:
            stock = UsStock(symbol)
        elif is_crypto:
            stock = Crypto(symbol)
        else:
            stock = KorStock(symbol)
        price = stock.get_price_now()
        price_layout = QHBoxLayout()
        price_now = round(float(price['c']), 2)
        price_label = QLabel(str(price_now))
        price_label.setFont(QFont('Arial', 14,  weight=QFont.Bold))

        change = float(price['d'])
        sign = ''
        if change > 0:
            color = 'green'
            sign = '+'
        elif change < 0:
            color = 'red'
        else:
            color = 'white'
        pct_change = round(float(price['dp']), 2)
        price_group = f'{sign}{change} ({pct_change}%)'
        price_info_label = QLabel(price_group)
        price_info_label.setStyleSheet(f'Color : {color}')
        plot = stock.draw_chart()
        price_layout.addWidget(price_label)
        price_layout.addWidget(price_info_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        layout.addWidget(plot)
        layout.addStretch()

        group_box.setLayout(layout)
        return group_box

    def draw_stock_info(self, stock):
        # stock = [country, symbol, name, crypto]
        if stock[3] == '1':  # check if stock is crypto
            crpyto_symbol = f'BINANCE:{stock[1]}USDT'
            stock_info = self.group(crpyto_symbol, stock[2], is_crypto=True)
            self.layout.addWidget(stock_info)
        else:
            if stock[0] == 'KOR':  # check if stock is in korea exchange
                stock_info = self.group(stock[1], stock[2], is_kor=True)
                self.layout.addWidget(stock_info)
            else:
                stock_info = self.group(stock[1], stock[2])
                self.layout.addWidget(stock_info)

    def add_row(self, value):
        row_item = [QStandardItem(item) for item in value]
        self.content.appendRow(row_item)
        self.draw_stock_info(value)

    def read_watchlist(self):
        watchlist_cnt = self.data.values.size
        if watchlist_cnt > 0:
            for value in self.data.values:
                self.add_row(value)

    def add_item(self):
        try:
            stock = self.stock.text()
            is_int_convertible = isinstance(int(stock), int)
            company = self.company.text()
            country = 'KOR'
        except:
            stock = self.stock.text().upper()
            company = self.company.text().title()
            country = 'USA'
        
        self.check_state = self.check_box.checkState()
        if self.check_state == 2:
            crypto = '1'
        else:
            crypto = ''
        data = [country, stock, company, crypto]

        if data[1] == '' or data[2] == '':
            self.alert('information', msg='Provide symbol and name.')
            return

        self.add_row(data)
        self.add_to_watchlist_csv(data)

        self.stock.clear()
        self.company.clear()
        self.stock.setFocus()
        self.check_box.setChecked(False)
        self.update_watchlist()

    def add_to_watchlist_csv(self, data):
        new_line = {k: v for k, v in zip(self.data.columns, data)}
        new_line = pd.DataFrame(new_line ,index=[0])
        self.data = pd.concat([self.data, new_line])

    def remove_item(self):
        selected = self.table.selectedIndexes()
        selected_row_idx = selected[0].row()
        if not selected:
            self.alert('information', msg='No item selected.')
            return

        symbol_name = self.data[['Symbol', 'Name']]
        selected_stock = symbol_name.iloc[selected_row_idx].values
        msg = f"Remove {selected_stock[0]} ({selected_stock[1]}) from watchlist?"
        option = self.alert('question', msg)
        if option == QMessageBox.Yes:
            self.data.drop(selected_row_idx, inplace=True)
            self.content.removeRows(selected_row_idx, 1)
            self.layout.takeAt(selected_row_idx).widget().deleteLater()
            self.update_watchlist()

    def update_watchlist(self):
        self.data.reset_index(drop=True, inplace=True)

    def alert(self, type, msg: str=None):
        if type == 'information':
            option = QMessageBox.information(
                self,
                'QMessageBox',
                msg,
            )
        elif type == 'question':
            option = QMessageBox.question(
                self,
                'QMessageBox',
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
        return option

    def keyPressEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key_Q:
                self.close()
            elif e.key() == Qt.Key_W:
                self.hide()

    def hideEvent(self, QHideEvent):
        first_tab = self.tabs.widget(0)
        self.tabs.setCurrentWidget(first_tab)

    def closeEvent(self, QCloseEvent):
        self.data.to_csv(self.data_path, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = Window()

    icon_path = resource_path('candlestick.ico')
    icon = QIcon(icon_path)
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    menu = QMenu()
    open_window = QAction('Open window')
    open_window.triggered.connect(window.show)
    menu.addAction(open_window)

    quit_app = QAction('Quit')
    quit_app.triggered.connect(app.quit)
    menu.addAction(quit_app)
    
    tray.setContextMenu(menu)

    window.show()
    sys.exit(app.exec_())
