 #  _____ _______         _                      _
 # |_   _|__   __|       | |                    | |
 #   | |    | |_ __   ___| |___      _____  _ __| | __  ___ ____
 #   | |    | | '_ \ / _ \ __\ \ /\ / / _ \| '__| |/ / / __|_  /
 #  _| |_   | | | | |  __/ |_ \ V  V / (_) | |  |   < | (__ / /
 # |_____|  |_|_| |_|\___|\__| \_/\_/ \___/|_|  |_|\_(_)___/___|
 #                                _
 #              ___ ___ ___ _____|_|_ _ _____
 #             | . |  _| -_|     | | | |     |  LICENCE
 #             |  _|_| |___|_|_|_|_|___|_|_|_|
 #             |_|
 #
 # IT ZPRAVODAJSTVÍ  <>  PROGRAMOVÁNÍ  <>  HW A SW  <>  KOMUNITA
 #
 # Tento zdrojový kód je součástí výukových seriálů na
 # IT sociální síti WWW.ITNETWORK.CZ
 #
 # Kód spadá pod licenci prémiového obsahu a vznikl díky podpoře
 # našich členů. Je určen pouze pro osobní užití a nesmí být šířen.
 # Více informací na http://www.itnetwork.cz/licence

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import datetime
from dateutil.relativedelta import relativedelta
import atexit
import pandas as pd
import os

# Formulář pro vytvoření nové osoby
class OsobaForm(QtWidgets.QWidget):    

    def __init__(self, **kwargs):
        super(OsobaForm, self).__init__(**kwargs)

        # Titulek a ikonka
        self.setWindowTitle("Přidat osobu")
        self.setWindowIcon(QtGui.QIcon("person_bg.png"))
        layoutFormulare = QtWidgets.QVBoxLayout()
        self.setLayout(layoutFormulare)

        # Layout s obrázkem
        self.obrazekLabel = QtWidgets.QLabel()
        self.obrazekLabel.setPixmap(QtGui.QPixmap("person_bg.png").scaledToWidth(150))
        obrazekLayout = QtWidgets.QHBoxLayout()
        obrazekLayout.addStretch()
        obrazekLayout.addWidget(self.obrazekLabel)
        obrazekLayout.addStretch()
        layoutFormulare.addLayout(obrazekLayout)

        # Layout se jménem
        self.udajeLayout = QtWidgets.QFormLayout()
        self.jmenoTextBox = QtWidgets.QLineEdit()
        # Přidáme řádek
        self.udajeLayout.addRow(QtWidgets.QLabel("Jméno"), self.jmenoTextBox)

        # Layout pro výběr data
        datumLayout = QtWidgets.QHBoxLayout()
        self.den = QtWidgets.QComboBox()
        self.den.addItem("Den")
        datumLayout.addWidget(self.den)
        self.mesic = QtWidgets.QComboBox()
        self.mesic.addItem("Měsíc")      
        datumLayout.addWidget(self.mesic)
        self.rok = QtWidgets.QComboBox()
        self.rok.addItem("Rok")
        datumLayout.addWidget(self.rok)
        self.napln_datum_boxy()

        # Přidáme řádek
        self.udajeLayout.addRow(QtWidgets.QLabel("Datum narození"), datumLayout)
        self.okButton = QtWidgets.QPushButton("Ok")
        self.udajeLayout.addRow(None, self.okButton)

        layoutFormulare.addLayout(self.udajeLayout)
       
        self.okButton.clicked.connect(self.ok_clicked)

    def setup(self):
        self.spravceOsob = root.spravceOsob
        self.prehled_form = root.prehled_form

    # Vygeneruje dny, měsíce a roky do comboboxů pro zadání data narození nové osoby
    def napln_datum_boxy(self):
        rok = int(datetime.datetime.now().year)
        for i in range(1, 32):
            self.den.addItem(str(i))
        for i in range(1, 13):
            self.mesic.addItem(str(i))
        for i in range(rok, rok - 190, -1):
            self.rok.addItem(str(i))

    def ok_clicked(self):
        if self.rok.currentText() == "Rok" or self.mesic.currentText() == "Mesic" or self.den.currentText() == "Den":
            self.jmenoTextBox.setText("ZADEJ DATUM!")
        else:
            self.spravceOsob.pridej(self.jmenoTextBox.text(), self.get_datum())
            self.prehled_form.update_osob()
            self.close()

    def clear_me(self):
        self.jmenoTextBox.setText("")
        self.den.setCurrentText("Den")
        self.mesic.setCurrentText("Měsíc")
        self.rok.setCurrentText("Rok")

    def get_datum(self):
        den = self.den.currentText()
        mesic = self.mesic.currentText()
        rok = self.rok.currentText()
        datum = datetime.datetime.strptime("{den} {mesic} {rok}".format(den = den, mesic = mesic, rok = rok), "%d %m %Y")
        return datum

# Formulář s přehledem osob a jejich narozenin
class PrehledForm(QtWidgets.QMainWindow):

    def __init__(self, **kwargs):
        super(PrehledForm, self).__init__(**kwargs)

        # Titul, ikonka a minimální šířka okna
        self.setWindowTitle("Výročí")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setMinimumWidth(650)

        # Vytvoříme hlavní widget a nastavíme BoxLayout
        formular = QtWidgets.QWidget()
        layoutFormulare = QtWidgets.QVBoxLayout()
        formular.setLayout(layoutFormulare)
        self.setCentralWidget(formular)

        # Vytvoříme informační box s BoxLayoutem (Dnešní datum)
        self.dnesLayout = QtWidgets.QHBoxLayout()
        layoutFormulare.addLayout(self.dnesLayout)
        self.dnesLayout.addWidget(QtWidgets.QLabel("Dnes je:"))
        self.dnesLayout.addStretch()
        self.dnesLabel = QtWidgets.QLabel(self.get_current_date())
        self.dnesLayout.addWidget(self.dnesLabel)

        # Vytvoříme informační box s BoxLayoutem (Nejbližší narozeniny)
        self.narozeninyLayout = QtWidgets.QHBoxLayout()
        layoutFormulare.addLayout(self.narozeninyLayout)
        self.narozeninyLayout.addWidget(QtWidgets.QLabel("Nejbližší narozeniny:"))
        self.narozeninyLayout.addStretch()
        self.nejblizsiLabel = QtWidgets.QLabel("")
        self.narozeninyLayout.addWidget(self.nejblizsiLabel)

        # Společný layout pro osobyListBox a narozenMonthCalendar
        self.prostredniLayout = QtWidgets.QHBoxLayout()
        layoutFormulare.addLayout(self.prostredniLayout)
       
        # Vytvoříme layout pro osobyListBox
        self.jmenaLayout = QtWidgets.QHBoxLayout()
        self.osobyListBox = QtWidgets.QListWidget()
        self.jmenaLayout.addWidget(self.osobyListBox)
        self.prostredniLayout.addLayout(self.jmenaLayout)

        # Vytvoříme layout pro narozenMonthCalendar
        self.kalendarLayout = QtWidgets.QVBoxLayout()
        self.narozenMonthCalendar = QtWidgets.QCalendarWidget(self)
        self.narozenMonthCalendar.setEnabled(False)        
               
        # Vytvoříme layout pro informace o osobách
        self.osobaLayout = QtWidgets.QHBoxLayout()
        self.osobaLayout.addWidget(QtWidgets.QLabel("Narozen:"))
        self.osobaLayout.addStretch()
        self.narozeninyLabel = QtWidgets.QLabel("")
        self.osobaLayout.addWidget(self.narozeninyLabel)
        self.kalendarLayout.addLayout(self.osobaLayout)
        self.osobaLayout2 = QtWidgets.QHBoxLayout()
        self.osobaLayout2.addWidget(QtWidgets.QLabel("Věk:"))
        self.osobaLayout2.addStretch()
        self.vekLabel = QtWidgets.QLabel("")
        self.osobaLayout2.addWidget(self.vekLabel)
        
        self.kalendarLayout.addLayout(self.osobaLayout2)
        self.kalendarLayout.addWidget(self.narozenMonthCalendar)
        self.prostredniLayout.addLayout(self.kalendarLayout)

        # Přidávání tlačítek
        self.tlacitkaLayout = QtWidgets.QHBoxLayout()
        self.pridatButton = QtWidgets.QPushButton("Přidat")
        self.pridatButton.setMinimumHeight(50)
        self.pridatButton.setIcon(QtGui.QIcon("pridej.png"))
        self.pridatButton.setIconSize(QtCore.QSize(32,32))
        self.odebratButton = QtWidgets.QPushButton("Odebrat")
        self.odebratButton.setMinimumHeight(50)
        self.odebratButton.setIcon(QtGui.QIcon("odeber.png"))
        self.odebratButton.setIconSize(QtCore.QSize(32,32))
        self.tlacitkaLayout.addWidget(self.pridatButton)
        self.tlacitkaLayout.addWidget(self.odebratButton)
        layoutFormulare.addLayout(self.tlacitkaLayout)
        self.pridatButton.clicked.connect(self.show_osoba_form)

        self.osobyListBox.currentItemChanged.connect(self.osoba_detail)
        self.odebratButton.clicked.connect(self.odebrat_osobu)
        
        self.show()

    def show_osoba_form(self):      
         self.osoba_form.show()
         self.osoba_form.clear_me()  

    # Vrátí aktuální datum česky jako string
    def get_current_date(self):
        return (str(datetime.datetime.now().day) + "." + str(datetime.datetime.now().month) 
        + "." + str(datetime.datetime.now().year))
	
    # Získá požadované instance
    def setup(self):
        self.osoba_form = root.osoba_form
        self.spravceOsob = root.spravceOsob

    def update_osob(self):
        self.osobyListBox.clear()
        for osoba in self.spravceOsob.osoby:
            self.osobyListBox.addItem(osoba.jmeno)
        if len(self.spravceOsob.osoby) > 0:
            self.nejblizsiLabel.setText("{} {}".format(self.spravceOsob.najdi_nejblizsi().jmeno, self.spravceOsob.najdi_nejblizsi().narozeniny.date().strftime("%d.%m.%Y")))
        else:
            self.nejblizsiLabel.setText("")
            self.narozeninyLabel.setText("")
            self.vekLabel.setText("")
            self.narozenMonthCalendar.setSelectedDate(QtCore.QDate(datetime.datetime.now()))

    def osoba_detail(self):
        if self.osobyListBox.currentRow() >= 0:
            osoba = self.spravceOsob.osoby[self.osobyListBox.currentRow()]
            self.vekLabel.setText(str(osoba.spocti_vek()))
            self.narozenMonthCalendar.setSelectedDate(QtCore.QDate(osoba.narozeniny))
            self.narozeninyLabel.setText(osoba.narozeniny.strftime("%d.%m.%Y"))

    def odebrat_osobu(self):
        if self.osobyListBox.currentRow() >= 0:
            del self.spravceOsob.osoby[self.osobyListBox.currentRow()]
            self.update_osob()

# Reprezentuje jednu osobu
class Osoba():

    # Konstruktor
    def __init__(self, jmeno, narozeniny):
        self.jmeno = jmeno
        self.narozeniny = narozeniny

    # Vrátí věk osoby
    def spocti_vek(self):
        dnes = datetime.datetime.now()
        vek = dnes.year - self.narozeniny.year    
        if dnes < self.narozeniny.replace(year=self.narozeniny.year + vek):
            vek -= 1
        return vek

    # Vrátí kolik dní zbývá do narozenin osoby
    def zbyva_dni(self):
        dnes = datetime.datetime.now()
        dalsi_narozeniny = self.narozeniny + relativedelta(years = self.spocti_vek() + 1)
        rozdil = dalsi_narozeniny - dnes
        return rozdil.days

    # Vrátí textovou reprezentaci osoby
    def __str__(self):
        return self.jmeno

# Slouží pro evidenci osob
class SpravceOsob():
    
    osoby = []

    def pridej(self, jmeno, datum_narozeni):
        osoba = Osoba(jmeno, datum_narozeni)
        self.osoby.append(osoba)

    def odeber(self, osoba):
        self.osoby.remove(osoba)

    def najdi_nejblizsi(self):
        if len(self.osoby) > 0:
            serazene = sorted(self.osoby, key = lambda item: item.zbyva_dni())
            return serazene[0]
        return None

    def uloz(self):       
        data = pd.DataFrame(columns = ["jmeno", "narozen"])
        for osoba in self.osoby:
            data = data.append(pd.DataFrame([[osoba.jmeno, osoba.narozeniny.strftime("%d.%m.%Y")]], columns = ["jmeno", "narozen"]), ignore_index = True)
        data.to_csv("osoby.csv", encoding='utf-8')

    def nacti(self):
        if os.path.exists("osoby.csv"):
            data = pd.read_csv("osoby.csv")
            if data.shape[0] > 0:
                for i in range(data.shape[0]):
                    self.pridej(data["jmeno"][i], datetime.datetime.strptime(data["narozen"][i], "%d.%m.%Y"))                
            
# Reprezentuje aplikaci
class App(QtWidgets.QApplication):

    def __init__(self):
        super(App, self).__init__(sys.argv)

    def build(self):
        self.prehled_form = PrehledForm()
        self.osoba_form = OsobaForm()
        self.spravceOsob = SpravceOsob()
        self.prehled_form.setup()
        self.osoba_form.setup()
        self.spravceOsob.nacti()
        self.prehled_form.update_osob()
        atexit.register(lambda: self.spravceOsob.uloz())
        sys.exit(self.exec_())

root = App()
root.build()
