from PyQt5 import QtGui, QtWidgets


def createIntroPage():
    page = QtWidgets.QWizardPage()
    page.setTitle("Introduction")

    label = QtWidgets.QLabel("This wizard will help you register your copy of "
            "Super Product Two.")
    label.setWordWrap(True)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


def createRegistrationPage():
    page = QtWidgets.QWizardPage()
    page.setTitle("Registration")
    page.setSubTitle("Please fill both fields.")

    nameLabel = QtWidgets.QLabel("Name:")
    nameLineEdit = QtWidgets.QLineEdit()

    emailLabel = QtWidgets.QLabel("Email address:")
    emailLineEdit = QtWidgets.QLineEdit()

    layout = QtWidgets.QGridLayout()
    layout.addWidget(nameLabel, 0, 0)
    layout.addWidget(nameLineEdit, 0, 1)
    layout.addWidget(emailLabel, 1, 0)
    layout.addWidget(emailLineEdit, 1, 1)
    page.setLayout(layout)

    return page


def createConclusionPage():
    page = QtWidgets.QWizardPage()
    page.setTitle("Conclusion")

    label = QtWidgets.QLabel("You are now successfully registered. Have a nice day!")
    label.setWordWrap(True)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    wizard = QtWidgets.QWizard()
    wizard.addPage(createIntroPage())
    wizard.addPage(createRegistrationPage())
    wizard.addPage(createConclusionPage())

    wizard.setWindowTitle("Trivial Wizard")
    wizard.show()

    sys.exit(wizard.exec_())