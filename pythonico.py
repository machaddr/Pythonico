#!/usr/bin/python3

import sys, keyword, importlib, re, webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtconsole.console import PythonConsole

# Create a custom widget to display line numbers
class LineCountWidget(QtWidgets.QTextEdit):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setReadOnly(True)

        font = QtGui.QFont("Monospace", 11)
        self.setFont(font)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setStyleSheet("background-color: lightgray;")

        # Connect textChanged signal
        self.editor.textChanged.connect(self.update_line_count)

        # Connect the valueChanged signal of the
        # to the update_line_count slot editor's vertical scroll bar
        self.editor.verticalScrollBar().valueChanged.connect(
            self.update_line_count
        )

        self.editor.cursorPositionChanged.connect(self.update_line_count)

        # Initial update of line count
        self.update_line_count()

    def update_line_count(self):
        # Get the total number of lines in the editor
        total_lines = self.editor.blockCount()

        # Get the first visible block
        first_visible_block = self.editor.firstVisibleBlock()
        first_visible_line = first_visible_block.blockNumber()

        # Get the number of visible lines
        visible_lines = self.editor.viewport().height() // self.editor.fontMetrics().height()

        # Calculate the maximum line number width
        max_line_number_width = len(str(total_lines))

        # Generate the line numbers
        lines = ""
        for line_number in range(first_visible_line + 1, first_visible_line + visible_lines + 1):
            if line_number <= total_lines:
                lines += str(line_number).rjust(max_line_number_width) + "\n"

        self.setPlainText(lines)

        # Adjust the width of the LineCountWidget based on the maximum line number width
        line_number_width = self.fontMetrics().width("9" * max_line_number_width)
        self.setFixedWidth(line_number_width + 10)

class AutoIndentFilter(QtCore.QObject):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and obj is self.editor:
            if event.key() == QtCore.Qt.Key_Tab:
                self.autoIndent()
                return True
            elif (
                event.key() == QtCore.Qt.Key_Return or
                event.key() == QtCore.Qt.Key_Enter
                ):
                self.handleEnterKey()
                return True

        return super().eventFilter(obj, event)

    def autoIndent(self):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            cursor.insertText('\t')
        else:
            lines = selected_text.split('\n')
            indented_lines = ['\t' + line if line.strip() else line
                for line in lines]
            indented_text = '\n'.join(indented_lines)
            cursor.insertText(indented_text)

        self.editor.setTextCursor(cursor)

    def handleEnterKey(self):
        cursor = self.editor.textCursor()
        block = cursor.block()
        previous_indentation = len(block.text()) - len(
            block.text().lstrip())

        cursor.insertText('\n' + ' ' * previous_indentation)

        # Check if the current line ends with a colon, indicating
        # a function or class declaration
        current_line = block.text().strip()
        if current_line.endswith(':') and current_line != ' ':
            # Add additional indentation for the new line
            cursor.insertText(' ' * 4)
        self.editor.setTextCursor(cursor)

class SyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Define the highlighting rules
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QtGui.QTextCharFormat()

        # Blue color for keywords
        keyword_format.setForeground(QtGui.QColor("#0000FF"))
        keyword_format.setFontWeight(QtGui.QFont.Bold)

        keywords = keyword.kwlist
        self.add_keywords(keywords, keyword_format)

        # String format
        string_format = QtGui.QTextCharFormat()

        # Green color for strings
        string_format.setForeground(QtGui.QColor("#a2cc89"))

        # Double-quoted strings
        self.add_rule(QtCore.QRegularExpression(r'".*?"'),
            string_format)

        # Single-quoted strings
        self.add_rule(QtCore.QRegularExpression(r"'.*?'"),
            string_format)

        # Comment format
        comment_format = QtGui.QTextCharFormat()

        # Brown color for comments
        comment_format.setForeground(QtGui.QColor("#873E23"))

        # Comments starting with #
        self.add_rule(QtCore.QRegularExpression(r"#.*"),
            comment_format)

    def add_keywords(self, keywords, format):
        for word in keywords:
            pattern = QtCore.QRegularExpression(
                r"\b" + word + r"\b")
            self.add_rule(pattern, format)

    def add_rule(self, pattern, format):
        rule = (pattern, format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern.match(text)
            while expression.hasMatch():
                start = expression.capturedStart()
                length = expression.capturedLength()
                self.setFormat(start, length, format)
                expression = pattern.match(text,
                    expression.capturedEnd())

class AboutLicenseDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License")

        self.setGeometry(100, 100, 450, 300)
        self.setMinimumSize(450, 300)
        self.setMaximumSize(450, 300)

        self.license = QtWidgets.QTextEdit()
        self.license.setReadOnly(True)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.license)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Center the window on the screen
        self.center()

        # Set the license text in the QtWidgets.QTextEdit
        self.license.setPlainText("""
        Copyright (c) 2024 André Machado

        This program is free software; you can redistribute it and/or modify
        it under the terms of the GNU General Public License version 2
        as published by the Free Software Foundation.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program; if not, write to the Free Software
        Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
        MA 02110-1301, USA.
        """)

    def center(self):
        # Get the screen geometry
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        window_geometry = self.frameGeometry()

        # Calculate the center position
        x = screen_geometry.width() // 2 - window_geometry.width() // 2
        y = screen_geometry.height() // 2 - window_geometry.height() // 2

        # Move the window to the center position
        self.move(x, y)

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Pythonico")

        layout = QtWidgets.QVBoxLayout()

        # Set the maximum size to the current size
        self.setMaximumSize(self.size())

        image_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("icons/main.png").scaledToWidth(200)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(image_label)

        about_text = """
            <h1><center>Pythonico</center></h1>
            <p>Pythonico is a Simple Text Editor for Python Language</p>
            <p>License: GNU GENERAL PUBLIC LICENSE Version 2</p>
            <p>Version: 1.0</p>
            <p>Author: André Machado</p>
        """
        about_label = QtWidgets.QLabel(about_text)
        layout.addWidget(about_label)

        self.setLayout(layout)

class Pythonico(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        # Add the current_file attribute and initialize it as None
        self.current_file = None

    def initUI(self):
        self.setWindowTitle("Pythonico")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(640, 400)

        # Set the window icon
        icon = QtGui.QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a QtWidgets.QSplitter widget to hold the editor and terminals
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # Create the plain text editor widget
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_widget)
        self.editor = QtWidgets.QPlainTextEdit()

        # Create LineCountWidget instance
        self.line_count = LineCountWidget(self.editor)
        self.editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # Add LineCountWidget to the editor layout
        editor_layout.addWidget(self.line_count)
        editor_layout.addWidget(self.editor)
        main_splitter.addWidget(editor_widget)

        # Create a sub-splitter for the terminals
        terminal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Initialize Xonsh console
        self.terminal = PythonConsole()
        
        # Redirect stdout and stderr to the console
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        # Start the console in a separate thread
        self.terminal.eval_in_thread()
        
        self.terminal.show()

        terminal_splitter.addWidget(self.terminal)

        main_splitter.addWidget(terminal_splitter)

        self.setCentralWidget(main_splitter)

        # Create a SyntaxHighlighter instance and associate it
        # with the text editor's document
        self.highlighter = SyntaxHighlighter(self.editor.document())

        # Set the width of the editor widget within the splitter
        main_splitter.setSizes([600, 300])
        self.setCentralWidget(main_splitter)

        # Set the background color to light yellow
        self.editor.setStyleSheet(
            "background-color: rgb(253, 246, 227);")

        # Set font size and font type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = self.editor.font()
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        self.filter = AutoIndentFilter(self.editor)
        self.editor.installEventFilter(self.filter)

        # Create a menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_file_action = QtWidgets.QAction("New File", self)
        new_file_action.setShortcut(QtGui.QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.createNewFile)
        file_menu.addAction(new_file_action)

        open_file_action = QtWidgets.QAction("Open", self)
        open_file_action.setShortcut(QtGui.QKeySequence.Open)
        open_file_action.triggered.connect(self.openFile)
        file_menu.addAction(open_file_action)

        save_file_action = QtWidgets.QAction("Save", self)
        save_file_action.setShortcut(QtGui.QKeySequence.Save)
        # Changed the method name to save_file
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        # Create the "Save As" action
        save_as_action = QtWidgets.QAction("Save As", self)
        save_as_action.setShortcut(QtGui.QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QtWidgets.QAction("Undo", self)
        undo_action.setShortcut(QtGui.QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QtWidgets.QAction("Redo", self)
        redo_action.setShortcut(QtGui.QKeySequence.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        cut_action = QtWidgets.QAction("Cut", self)
        cut_action.setShortcut(QtGui.QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QtWidgets.QAction("Copy", self)
        copy_action.setShortcut(QtGui.QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QtWidgets.QAction("Paste", self)
        paste_action.setShortcut(QtGui.QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_all_action = QtWidgets.QAction("Select All", self)
        select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Find menu
        find_menu = menubar.addMenu("&Find")

        find_action = QtWidgets.QAction("Find", self)
        find_action.setShortcut(QtGui.QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        find_menu.addAction(find_action)

        find_next_action = QtWidgets.QAction("Find Next", self)
        find_next_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+F"))
        # find_next_action.triggered.connect(self.findNext)
        find_menu.addAction(find_next_action)

        find_previous_action = QtWidgets.QAction("Find Previous", self)
        find_previous_action.setShortcut(QtGui.QKeySequence("Ctrl+Alt+F"))
        # find_previous_action.triggered.connect(self.findPrevious)
        find_menu.addAction(find_previous_action)

        # Add a separator
        find_menu.addSeparator()

        go_to_line_action = QtWidgets.QAction("Go to Line", self)
        go_to_line_action.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        go_to_line_action.triggered.connect(self.goToLine)
        find_menu.addAction(go_to_line_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        terminal_action = QtWidgets.QAction("Toggle Terminal", self)
        terminal_action.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        terminal_action.triggered.connect(self.toggleTerminal)
        view_menu.addAction(terminal_action)

        # Add a separator
        view_menu.addSeparator()

        splitHorizontalAction = QtWidgets.QAction(QtGui.QIcon(),
            "Split Horizontal", self)
        splitHorizontalAction.setShortcut("Ctrl+%")
        # splitHorizontalAction.triggered.connect(self.splitHorizontal)
        view_menu.addAction(splitHorizontalAction)

        splitVerticalAction = QtWidgets.QAction(QtGui.QIcon(),
            "Split Vertical", self)
        splitVerticalAction.setShortcut("Ctrl+/")
        # splitVerticalAction.triggered.connect(self.splitVertical)
        view_menu.addAction(splitVerticalAction)

        # Run menu
        run_menu = menubar.addMenu("&Run")

        run_action = QtWidgets.QAction("Run", self)
        run_action.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.runProgram)
        run_menu.addAction(run_action)

        help_menu = menubar.addMenu("&Help")

        website_action = QtWidgets.QAction("Website", self)
        website_action.triggered.connect(self.showWebsiteDialog)
        help_menu.addAction(website_action)

        # Add a separator
        help_menu.addSeparator()

        license_action = QtWidgets.QAction("License", self)
        license_action.triggered.connect(self.showLicenseDialog)
        help_menu.addAction(license_action)

        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)

        # Create a status bar
        self.statusBar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("  Ready")

        # Connect the textChanged signal of the editor to a slot
        self.editor.textChanged.connect(self.updateStatusBar)

        # Connect the onTextChanged slot to the
        # textChanged signal of the editor
        self.editor.textChanged.connect(self.onTextChanged)

        # Connect cursorPositionChanged signal
        self.editor.cursorPositionChanged.connect(self.updateStatusBar)

        self.show()

    def createNewFile(self):
        # Create a plain text editor widget
        editor = QtWidgets.QPlainTextEdit(self)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Set the background color to light yellow
        editor.setStyleSheet("background-color: rgb(253, 246, 227);")

        # Set font size and font type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = editor.font()
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        # Setup New File Window Name
        self.setWindowTitle(f"Pythonico - New File")

        # Sets an empty File
        self.current_file = None
        self.editor.clear()

    def openFile(self):
        home_dir = QtCore.QDir.homePath()

        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)

        # Set the default directory to home screen
        file_dialog.setDirectory(home_dir)

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text = text_stream.readAll()
                file.close()
                self.editor.setPlainText(text)

                # Update current_file attribute
                self.current_file = file_path
                # Update window title
                self.setWindowTitle(f"Pythonico - {self.current_file}")

    def save_file(self):
        if self.current_file:
            file_path = self.current_file
        else:
            # No current file is set, prompt the user
            # to choose a file to save
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                "Save File")
            if not file_path:
                # User canceled the file selection, return without saving
                return

        file = QtCore.QFile(file_path)
        if file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            text_stream = QtCore.QTextStream(file)
            text_stream << self.editor.toPlainText()
            file.close()
            self.current_file = file_path
            self.setWindowTitle(f"Pythonico - {self.current_file}")

    def save_as_file(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self,
            "Write File:")
        if file_path:
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream << self.editor.toPlainText()
                file.close()

    def onTextChanged(self):
        # Add an asterisk (*) to the window title to indicate unsaved changes
        if self.current_file:
            self.setWindowTitle(f"Pythonico - {self.current_file} *")
        else:
            self.setWindowTitle("Pythonico *")

    def showWebsiteDialog(self):
        webbrowser.open("https://github.com/machaddr/pythonico")

    def showLicenseDialog(self):
        show_license = AboutLicenseDialog()
        show_license.exec_()

    def showAboutDialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def toggleTerminal(self):
        if self.terminal.isHidden():
            self.terminal.show()
        else:
            self.terminal.hide()

    def splitVertical(self):
        splitterV = QtWidgets.QSplitter(Qt.Vertical)
        self.splitterV.addWidget(QtWidgets.QTextEdit(self))

    def splitHorizontal(self):
        splitterH = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitterH.addWidget(QtWidgets.QTextEdit(self))

    def updateStatusBar(self):
        cursor = self.editor.textCursor()

        # Current line number
        block_number = cursor.blockNumber() + 1

        # Total line numbers
        total_lines = self.editor.document().blockCount()

        # Current column number
        column = cursor.columnNumber() + 1
        text = self.editor.toPlainText()

        # Count the total number of words
        words = text.split()
        word_count = len(words)

        # Get the current date
        current_date = QtCore.QDate.currentDate() \
            .toString(QtCore.Qt.DefaultLocaleLongDate)

        # Get the current time
        current_time = QtCore.QTime.currentTime() \
            .toString(QtCore.Qt.DefaultLocaleShortDate)

        # Update the status bar text
        status_text = (
            f" |  Line: {block_number}/{total_lines}  "
            f"| Column: {column}  |  Words: {word_count}  "
            f"|  {current_date} {current_time} |"
        )

        # Update the status bar message
        self.statusBar.showMessage(status_text)

    def copyText(self):
        self.terminal.copy()

    def pasteText(self):
        self.terminal.paste()

    def runProgram(self):
        try:
            content = self.editor.toPlainText()
            if not content:
                QtWidgets.QMessageBox.warning(self,
                    "Current Text Stream is Empty",
                    "The Editor is Empty. Please Type Some Python Code!")
            else:
                # Push the code to the local namespace
                self.terminal.push_local_ns('code', content)
                # Now run the code in the console
                self.terminal.eval_in_thread()  # No parameters
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,
                "Unhandled Python Exception",
                f"An error occurred: {e}")

            
    def show_find_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Find")
        layout = QtWidgets.QVBoxLayout(dialog)

        search_input = QtWidgets.QLineEdit(dialog)
        layout.addWidget(search_input)

        options_layout = QtWidgets.QVBoxLayout()

        find_button = QtWidgets.QPushButton("Find", dialog)
        find_button.clicked.connect(lambda: self.find_text(
            search_input.text()))
        options_layout.addWidget(find_button)

        layout.addLayout(options_layout)
        dialog.exec_()

    def find_text(self, search_text):
        flags = re.MULTILINE

        cursor = self.editor.textCursor()

        start_pos = (
            cursor.selectionEnd()
            if cursor.hasSelection()
            else cursor.position()
        )
        search_range = range(start_pos + 0, len(self.editor.toPlainText()))

        pattern = re.compile(search_text, flags)

        for pos in search_range:
            match = pattern.search(self.editor.toPlainText(), pos)
            if match:
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(),
                    QtGui.QTextCursor.KeepAnchor)
                self.editor.setTextCursor(cursor)
                self.editor.setFocus()

                return

        # If no match found, wrap around to the beginning and search again
            if len(search_range) > 0:
                for pos in range(search_range[0]):
                    match = pattern.search(self.editor.toPlainText(), pos)
                    if match:
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(),
                            QtGui.QTextCursor.KeepAnchor)
                        self.editor.setTextCursor(cursor)
                        self.editor.setFocus()
                        return

        QtWidgets.QMessageBox.information(self, "Find",
            "No matches found.")

    def goToLine(self):
        max_lines = self.editor.document().blockCount()
        line, ok = QtWidgets.QInputDialog.getInt(self, "Go to Line",
            f"Line Number (1 - {max_lines}):", value=1, min=1,
                max=max_lines)
        if ok:
            if line > max_lines:
                QtWidgets.QMessageBox.warning(self,
                    "Invalid Line Number",
                    f"The maximum number of lines is {max_lines}.")
            else:
                cursor = self.editor.textCursor()
                cursor.setPosition(
                    self.editor.document().findBlockByLineNumber(line - 1). \
                    position())
                self.editor.setTextCursor(cursor)

                # Indentation adjustment
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                indent = len(cursor.block().text()) - len(cursor.block(). \
                    text().lstrip())
                cursor.movePosition(QtGui.QTextCursor.Right,
                    QtGui.QTextCursor.MoveAnchor, indent)
                self.editor.setTextCursor(cursor)
        else:
            self.showMessageBox("Go to Line canceled.")

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setText(message)
        msg_box.setWindowTitle("Go to Line")
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.addButton(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    sys.exit(app.exec_())
