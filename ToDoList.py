import os
import sys
import tkinter as tk
import datetime
import threading
import subprocess
from pathlib import Path  # Libreria nativa per gestire i percorsi in modo sicuro

# 1. Lista dei moduli richiesti e controllo/installazione automatica
required_modules = ["pystray", "pillow"]
modules = []

for module in required_modules:
    try:
        if module == "pillow":
            from PIL import Image
        else:
            __import__(module)
        modules.append(module)
    except ImportError:
        print(f"Modulo '{module}' mancante. Tentativo di installazione automatica...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            if module == "pillow":
                from PIL import Image
            else:
                __import__(module)
            modules.append(module)
            print(f"Modulo '{module}' installato con successo!")
        except Exception as e:
            print(f"Impossibile installare il modulo {module}: {e}")
            
            # Percorso di fallback per il log di installazione nella cartella utente
            home_dir = Path.home() / ".todolist"
            home_dir.mkdir(exist_ok=True)
            with open(home_dir / "errore_installazione_log.txt", "w") as file:
                file.write(f"Errore durante l'installazione di {module}: {e}")
            sys.exit(1)

# Importazioni globali ora che siamo sicuri che i moduli sono presenti
import pystray
from PIL import Image

class App:

    name = "To Do List"
    activities = []
    etichette = []
    n_activities = 0
    labels = []
    i = 0
    colonna = 0  # Inizia da 0 dentro il lista_frame
    error = 0
    error_label = None
    tray_icon = None
    app_version = "alpha1.0"

    # Definiamo la cartella dati sicura nella Home dell'utente (es. C:\Users\Nome\.todolist)
    DATA_DIR = Path.home() / ".todolist"
    LOGS_DIR = DATA_DIR / "logs"
    ACTIVITIES_FILE = DATA_DIR / "activities.txt"

    # Assegniamo la lista dei moduli caricati alla variabile di classe
    modules = modules

    main_page = tk.Tk()
    main_page.title(name)
    main_page.geometry("600x400")
    main_page.resizable(False, False)
    main_page.configure(background="white")

    # Frame per dividere la struttura
    main_frame = tk.Frame(main_page, bg="white")
    lista_frame = tk.Frame(main_page, bg="white")
    bottom_frame = tk.Frame(main_page, bg="white") 

    def create_window():
        # Creiamo le cartelle dati se non esistono ancora prima di avviares l'interfaccia
        App.DATA_DIR.mkdir(exist_ok=True)
        App.LOGS_DIR.mkdir(exist_ok=True)

        # Intercettiamo la "X" di Windows sulla finestra
        App.main_page.protocol("WM_DELETE_WINDOW", App.nascondi_nella_tray)

        # Posizioniamo i contenitori principali
        App.main_frame.pack(fill="x", padx=10, pady=5)
        App.lista_frame.pack(fill="both", expand=True, padx=10, pady=5)
        App.bottom_frame.pack(fill="x", side="bottom", padx=10, pady=5) 

        # Configura le colonne del bottom_frame per spingere i testi ai lati
        App.bottom_frame.grid_columnconfigure(0, weight=1)
        App.bottom_frame.grid_columnconfigure(1, weight=1)

        # Widget superiori inseriti correttamente dentro App.main_frame
        title_app = tk.Label(App.main_frame, text="To do List", font=("Impact", 20), fg="red", bg="white")
        title_app.grid(row=0, column=0, pady=10, padx=200, sticky="W")

        exit_button = tk.Button(App.main_frame, text="EXIT", font=("Arial", 14), bd=4, state="normal", cursor="hand2", command=App.chiudi_definitivo)
        exit_button.grid(row=0, column=0, pady=15, padx=450, sticky="W")

        register_activity_button = tk.Button(App.main_frame, text="Aggiungi attivita", font=("Arial", 10), bd=4, state="normal", cursor="hand2", command=App.register_activities)
        register_activity_button.grid(row=2, column=0, pady=0, padx=0, sticky="W")

        list_activity_title = tk.Label(App.main_frame, text="Lista attivita:", font=("Arial", 16), bg="white")
        list_activity_title.grid(row=1, column=0, pady=5, padx=0, sticky="W")

        App.text_input = tk.Entry(App.main_frame, font=("Arial", 14))
        App.text_input.grid(row=2, column=0, pady=0, padx=110, sticky="W")

        # Crediti e versione inseriti nel bottom_frame con grid sulla stessa riga (row=0)
        credits_app = tk.Label(App.bottom_frame, text="©2026 Not_xtemerario30", font=("Arial", 7), fg="black", bg="white")
        credits_app.grid(row=0, column=0, sticky="W")

        version_label = tk.Label(App.bottom_frame, text=f"v{App.app_version}", font=("Arial", 7), fg="black", bg="white")
        version_label.grid(row=0, column=1, sticky="E")

        App.main_page.mainloop()


    def register_activities():
        text = App.text_input.get()

        try:
            if App.error == 1 and App.error_label is not None:
                App.error_label.destroy()
                App.error = 0

            if text != "":   
                App.activities.append(Activity(text, 1))
                App.write_activity(text) # Salva l'attività nel percorso sicuro
                
                # Creiamo l'etichetta SOLO dentro lista_frame, usando l'indice corrente App.i
                App.labels.append(tk.Label(App.lista_frame, text=(f"n.{App.i+1}) {App.activities[App.i].name_activity}"), bg="white", font=("Arial", 11)))
                App.labels[App.i].grid(row=App.colonna, column=0, pady=2, padx=5, sticky="W")
                
                App.colonna = App.colonna + 1
                App.i = App.i + 1
                App.text_input.delete(0, tk.END) # Svuota il campo di input
            else:
                App.error_label = tk.Label(App.main_frame, text="Inserire il nome di una attivita!", font=("Impact", 14), fg="red", bg="white")
                App.error_label.grid(row=1, column=0, pady=0, padx=150, sticky="W")
                App.error = 1
        except Exception as e:
            App.write_log(e)

    def write_log(message):
        data = datetime.datetime.now()
        data_string = data.strftime("%d%m%Y%H%M%S")

        # Assicuriamoci che la cartella dei log esista nel percorso sicuro dell'utente
        App.LOGS_DIR.mkdir(exist_ok=True)

        with open(App.LOGS_DIR / f"To_Do_List_{data_string}_log.txt", "w", encoding="utf-8") as file:
            file.write(f"{data.hour}:{data.minute}:{data.second} - {message}")

    def write_activity(name_activity):
        with open(App.ACTIVITIES_FILE, "a", encoding="utf-8") as file:
            file.write(f"{name_activity}\n")

    def nascondi_nella_tray():
        App.main_page.withdraw()
        if not App.tray_icon:
            image = Image.new('RGB', (64, 64), color='red')
            menu = pystray.Menu(
                pystray.MenuItem('Apri', App.mostra_finestra),
                pystray.MenuItem('Esci', App.chiudi_definitivo)
            )
            App.tray_icon = pystray.Icon("todolist", image, "To Do List", menu)
            threading.Thread(target=App.tray_icon.run, daemon=True).start()
        else:
            App.tray_icon.visible = True

    def mostra_finestra():  
        if App.tray_icon:
            App.tray_icon.visible = False
        App.main_page.deiconify()

    def chiudi_definitivo():
        if App.tray_icon:
            App.tray_icon.stop()
        App.main_page.destroy()


class Activity:
    name_activity = ""
    def __init__(self, name_activity, priority):
        self.name_activity = name_activity
        self.priority = priority
        self.enable = True


# Avvio del programma
App.create_window()