from unicurses import *
from PIL import Image
import zipfile
import json
import sys
import io
import os

class Properties:
    def __init__(self, fps, width, height, reverse_chars, print_result, chars, image, image_path):
        self.fps = fps
        self.width = width
        self.reverse_chars = reverse_chars
        self.print_result = print_result
        self.image = image
        self.image_path = image_path
        
        self._height = height
        self._chars = chars
    
    @property
    def height(self):
        if not self._height:
            original_height, original_width = self.image.size
            return int(self.width * original_height / original_width)
        return self._height

    @property
    def chars(self):
        return self._chars[::-1] if self.reverse_chars else self._chars
    
    @property
    def ms(self):
        return round(1000 / self.fps)

class ConfigurationManager:
    DEFAULT_CONFIG = {
        "fps": 24,
        "width": 80,
        "height": 40,
        "reverse_background": False,
        "print_result": True,
        "characters": " _,.:;-~+=*!?/[(&$#@"
    }
    
    EXPECTED_FILES = {
        os.path.basename(__file__),
        "run.bat",
        "README.md",
        "output.zip",
        "output.txt",
        "settings.json",
        "requirements.txt",
        "__pycache__"
    }

    def __init__(self):
        self._directory = os.path.dirname(os.path.realpath(__file__))
        self._files = os.listdir(self._directory)
        self._clean_up_previous_files()

    def _check_current_directory(self):
        unexpected_files = [
            file for file in self._files
            if not file.endswith((".gif", ".jpg", ".png")) and file not in self.EXPECTED_FILES
        ]

        if unexpected_files:
            sys.exit("Erro: Este arquivo deve ser inserido em uma pasta vazia.")

    def _validate_user_config(self, user_config):
        default_types = {k: type(v) for k, v in self.DEFAULT_CONFIG.items()}
        user_types = {k: type(v) for k, v in user_config.items()}
        
        if default_types != user_types or not 200 >= user_config.get("width", -1) > 0:
            sys.exit("Erro: O arquivo de configurações foi modificado incorretamente.")

    def _get_user_config(self):
        self._check_current_directory()
        if "settings.json" not in self._files:
            with open("settings.json", "w") as file:
                json.dump(self.DEFAULT_CONFIG, file, indent = 4)

        try:
            with open("settings.json") as data:
                user_config = json.load(data)
                self._validate_user_config(user_config)
        except Exception: sys.exit("Erro: Não foi possível ler o arquivo de configurações.")
        return user_config.values()

    def _get_user_image(self, width, height):
        os.system(f"MODE {width}, {height}")
        image_path = input("Insira um caminho válido para a imagem: ")
        try: image = Image.open(image_path)
        except Exception: sys.exit("Erro: O arquivo fornecido é inválido ou não pode ser aberto.")
        return image, image_path

    def _clean_up_previous_files(self):
        for file in self._files:
            if file in ("output.zip", "output.txt"):
                os.remove(os.path.join(self._directory, file))

    def get_properties(self):
        fps, width, height, reverse_chars, print_result, chars = self._get_user_config()
        image, image_path = self._get_user_image(width, height)
        return Properties(fps, width, height, reverse_chars, print_result, chars, image, image_path)

class ASCIIArtGenerator:
    def __init__(self):
        self._config_manager = ConfigurationManager()
        self._properties = self._config_manager.get_properties()
        self._select_processing_method()

    def _convert_to_ascii(self, image):
        image = image.resize((self._properties.width, self._properties.height)).convert("L")
        raw_text = "".join([
            self._properties.chars[int(color / (255 / (len(self._properties.chars) - 1)))]
            for color in image.getdata()
        ])

        return "\n".join([
            raw_text[i:(i + self._properties.width)]
            for i in range(0, len(raw_text), self._properties.width)
        ])

    def _handle_gif_conversion(self):
        ascii_frames = []
        memfile = io.BytesIO()

        with zipfile.ZipFile(memfile, "w", compression = zipfile.ZIP_DEFLATED) as zip_file:
            for frame in range(self._properties.image.n_frames):
                self._properties.image.seek(frame)
                ascii_art = self._convert_to_ascii(self._properties.image)

                ascii_frames.append(ascii_art)
                zip_file.writestr(f"output{frame + 1}.txt", str.encode(ascii_art, "utf-8"))

        with open("output.zip", "wb") as output_file:
            output_file.write(memfile.getvalue())

        if self._properties.print_result:
            initscr()
            timeout(self._properties.ms)
            curs_set(0)
            noecho()

            while True:
                for ascii_frame in ascii_frames:
                    mvaddstr(0, 0, ascii_frame.replace("\n", ""))
                    if getch() is ERR:
                        refresh()
                    else:
                        endwin()
                        return

    def _handle_image_conversion(self):
        ascii_art = self._convert_to_ascii(self._properties.image)
        with open("output.txt", "w") as output_file:
            output_file.write(ascii_art)

        if self._properties.print_result:
            initscr()
            curs_set(0)

            mvaddstr(0, 0, ascii_art.replace("\n", ""))
            getch()
            endwin()

    def _select_processing_method(self):
        try:
            match self._properties.image_path[self._properties.image_path.rfind(".") + 1:]:
                case "gif": self._handle_gif_conversion()
                case "jpg" | "png": self._handle_image_conversion()
                case _: sys.exit("Erro: O formato do arquivo fornecido não é suportado.")
        except: pass
        os.system("cls || clear")

def main():
    ASCIIArtGenerator()

if __name__ == "__main__":
    main()
 
