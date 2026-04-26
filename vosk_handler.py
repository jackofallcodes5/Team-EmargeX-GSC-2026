import os
import json
import zipfile
import requests
from vosk import Model, KaldiRecognizer, SpkModel
from tqdm import tqdm

class VoskHandler:
    def __init__(self, model_path="model", spk_model_path="model-spk"):
        self.model_path = os.path.abspath(model_path)
        self.spk_model_path = os.path.abspath(spk_model_path)
        
        # URLs for default small English model and speaker model
        self.MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        self.SPK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-spk-0.4.zip"

        self._ensure_models_exist()
        
        print("Loading VOSK models (this may take a moment)...")
        self.model = Model(self.model_path)
        self.spk_model = SpkModel(self.spk_model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.rec.SetSpkModel(self.spk_model)

    def _ensure_models_exist(self):
        """Check if models exist, download and unzip if not."""
        if not os.path.exists(self.model_path):
            self._download_and_unzip(self.MODEL_URL, "model_tmp.zip", self.model_path)
        if not os.path.exists(self.spk_model_path):
            self._download_and_unzip(self.SPK_MODEL_URL, "spk_tmp.zip", self.spk_model_path)

    def _download_and_unzip(self, url, zip_name, target_dir):
        print(f"Downloading model from {url}...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_name, "wb") as f, tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
            for data in response.iter_content(1024):
                f.write(data)
                pbar.update(len(data))
        
        print(f"Extracting {zip_name}...")
        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(".")
            # Rename the extracted folder to target_dir if needed
            extracted_dir = zip_ref.namelist()[0].split('/')[0]
            if extracted_dir != target_dir:
                os.rename(extracted_dir, target_dir)
        
        os.remove(zip_name)

    def process_chunk(self, chunk):
        """Process binary audio chunk and return (text, speaker_vector) if finalized."""
        if self.rec.AcceptWaveform(chunk):
            res = json.loads(self.rec.Result())
            text = res.get("text", "")
            spk_vector = res.get("spk", None)
            return text, spk_vector
        return None, None

    def get_partial(self):
        """Get partial transcription for live feedback."""
        res = json.loads(self.rec.PartialResult())
        return res.get("partial", "")
