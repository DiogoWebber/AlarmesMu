import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import time
import pygame
import threading
import os
import shutil
import sys

pygame.mixer.init()

if getattr(sys, 'frozen', False):
    direcao_do_arquivo = sys._MEIPASS
else:
    direcao_do_arquivo = os.path.dirname(os.path.abspath(__file__))

diretorio_audios = os.path.join(direcao_do_arquivo, "audios")
alarme_som = os.path.join(diretorio_audios, "naotrabalha.mp3")


def gerar_horarios():
    """Gera a lista de horários no formato HH:MM para 24 horas e associa os eventos com nomes."""
    horarios = []
    for hora in range(24):
        horarios.append({"hora": f"{hora:02d}:00", "tipo": "BC"})  # Eventos de hora em hora (BC)
        horarios.append({"hora": f"{hora:02d}:30", "tipo": "DS"})  # Eventos de 30 minutos (DS)
    return horarios


eventos = gerar_horarios()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Eventos")
        self.root.configure(bg="#f0f4f7")

        # Inicializa a lista de áudios
        self.audios = self.carregar_audios()

        # Configuração da janela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 500
        window_height = 400
        position_top = int((screen_height / 2) - (window_height / 2))
        position_right = int((screen_width / 2) - (window_width / 2))
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # Cabeçalho
        header_frame = tk.Frame(self.root, bg="#4e79a7")
        header_frame.pack(fill="x", pady=10)
        header_label = tk.Label(header_frame, text="Monitor de Eventos", fg="white", font=("Roboto", 16, "bold"), bg="#4e79a7")
        header_label.pack(pady=10)

        # Relógio e próximo evento
        self.horario_atual_label = tk.Label(self.root, text="", font=("Arial", 14), bg="#f0f4f7")
        self.horario_atual_label.pack(pady=10)

        self.proximo_evento_label = tk.Label(self.root, text="", font=("Arial", 14), bg="#f0f4f7")
        self.proximo_evento_label.pack(pady=10)

        # Menu de Áudios
        self.audio_selecionado = tk.StringVar()
        self.audio_selecionado.set(self.audios[0] if self.audios else "Sem áudios disponíveis")
        audio_frame = tk.Frame(self.root, bg="#f0f4f7")
        audio_frame.pack(pady=10)
        self.audio_menu = tk.OptionMenu(audio_frame, self.audio_selecionado, *self.audios)
        self.audio_menu.config(width=25)
        self.audio_menu.grid(row=0, column=0, padx=10)

        self.teste_audio_button = tk.Button(audio_frame, text="Testar Áudio", command=self.testar_audio, bg="#3e8e41", fg="white")
        self.teste_audio_button.grid(row=0, column=1, padx=(0, 50)) 
       
        # Controle de volume
        volume_frame = tk.Frame(self.root, bg="#f0f4f7")
        volume_frame.pack()

        volume_label = tk.Label(volume_frame, text="Volume:", bg="#f0f4f7")
        volume_label.pack(side=tk.TOP, pady=(0, 2))  # Coloca a palavra 'Volume' acima da barra, com espaço

        self.volume_slider = tk.Scale(
            volume_frame, from_=0, to=100, orient="horizontal", command=self.ajustar_volume, bg="#f0f4f7"
        )
        self.volume_slider.set(50)
        self.volume_slider.pack() 


        # Botões adicionais
        self.desligar_alarme_button = tk.Button(self.root, text="Desligar Áudio", command=self.desligar_audio, state=tk.DISABLED, bg="#e74c3c", fg="white")
        self.desligar_alarme_button.pack(pady=10)

        self.adicionar_audio_button = tk.Button(self.root, text="Adicionar Áudio", command=self.adicionar_audio, bg="#f39c12", fg="white")
        self.adicionar_audio_button.pack(pady=10)

        # Atualização e monitoramento
        self.atualizar_interface()
        threading.Thread(target=self.verificar_eventos, daemon=True).start()

    def ajustar_volume(self, volume):
        try:
            pygame.mixer.music.set_volume(int(volume) / 100)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ajustar volume: {e}")

    def carregar_audios(self):
        """Carrega os arquivos de áudio no diretório."""
        try:
            arquivos = os.listdir(diretorio_audios)
            audios = [arquivo for arquivo in arquivos if arquivo.endswith(('.mp3', '.wav'))]
            if not audios:
                messagebox.showerror("Erro", "Nenhum arquivo de áudio encontrado!")
            return audios
        except FileNotFoundError:
            messagebox.showerror("Erro", "Diretório de áudios não encontrado!")
            return []

    def atualizar_interface(self):
        """Atualiza o horário atual e o próximo evento."""
        horario_atual = datetime.datetime.now().strftime("%H:%M:%S")
        self.horario_atual_label.config(text=f"Hora atual: {horario_atual}")
        
        proximo_evento, tempo_restante, tipo_evento = self.calcular_proximo_evento()
        if proximo_evento:
            minutos, segundos = divmod(tempo_restante, 60)
            self.proximo_evento_label.config(
                text=f"Próximo evento ({tipo_evento}): {proximo_evento} ({minutos}m {segundos}s restantes)"
            )
        else:
            self.proximo_evento_label.config(text="Nenhum evento restante hoje.")
        
        # Atualiza novamente após 1 segundo (1.000 ms)
        self.root.after(1000, self.atualizar_interface)

    def calcular_proximo_evento(self):
        """Calcula o próximo evento e o tempo restante em segundos.""" 
        agora = datetime.datetime.now()
        for evento in eventos:
            hora_evento = datetime.datetime.strptime(evento["hora"], "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            if hora_evento > agora:
                tempo_restante = (hora_evento - agora).total_seconds()
                return evento["hora"], int(tempo_restante), evento["tipo"]
        return None, None, None

    def testar_audio(self):
        global alarme_som, audio_em_reproducao
        try:
            alarme_som = os.path.join(diretorio_audios, self.audio_selecionado.get())

            # Verifique se o arquivo de áudio existe antes de tentar carregar
            if not os.path.exists(alarme_som):
                raise FileNotFoundError(f"Arquivo de áudio não encontrado: {alarme_som}")

            pygame.mixer.music.load(alarme_som)
            pygame.mixer.music.play()
            audio_em_reproducao = True
            self.desligar_alarme_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao tocar o áudio: {e}")

    def tocar_alarme(self):
        """Reproduz o som do alarme e habilita o botão para desligar.""" 
        global alarme_som, audio_em_reproducao
        try:
            alarme_som = os.path.join(diretorio_audios, self.audio_selecionado.get())  # Carrega o áudio selecionado
            pygame.mixer.music.load(alarme_som)
            pygame.mixer.music.play(-1)  # Reproduz em loop
            audio_em_reproducao = True  # Marca o áudio como em reprodução
            self.desligar_alarme_button.config(state=tk.NORMAL)  # Habilita o botão "Desligar Áudio"

            if messagebox.askokcancel("Alarme", "Chegou a hora do evento!"):
                self.desligar_audio()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao tocar o áudio: {e}")

    def desligar_audio(self):
        """Para o som do áudio (teste ou alarme) e desabilita o botão.""" 
        global audio_em_reproducao
        try:
            pygame.mixer.music.stop()
            audio_em_reproducao = False  # Marca o áudio como parado
            self.desligar_alarme_button.config(state=tk.DISABLED)  # Desabilita o botão "Desligar Áudio"
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao desligar o áudio: {e}")

    def verificar_eventos(self):
        """Verifica continuamente o horário atual e toca o alarme nos horários configurados.""" 
        while True:
            agora = datetime.datetime.now()
            proximo_evento, tempo_restante, tipo_evento = self.calcular_proximo_evento()
            if proximo_evento and tempo_restante <= 0:
                self.tocar_alarme()
            time.sleep(1) 

    def adicionar_audio(self):
        """Permite ao usuário adicionar um novo arquivo de áudio."""
        arquivo_audio = filedialog.askopenfilename(filetypes=[("Arquivos de Áudio", "*.mp3;*.wav")])
        if arquivo_audio:
            nome_arquivo = os.path.basename(arquivo_audio)
            destino = os.path.join(diretorio_audios, nome_arquivo)
            if not os.path.exists(diretorio_audios):
                os.makedirs(diretorio_audios)
            shutil.copy(arquivo_audio, destino)
            self.audios = self.carregar_audios()
            self.audio_selecionado.set(self.audios[0])  

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
