import importlib
import os


class MLModels:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._models = {}
        return cls._instance

    def _lazy_load(self, name, loader):
        if name not in self._models:
            print(f"Loading ML model: {name}...")
            self._models[name] = loader()
            print(f"Loaded: {name}")
        return self._models[name]

    def load_all(self):
        if self._loaded:
            return
        print("ML models set to lazy-load (will load on first use).")
        self._loaded = True

    def get_skill_encoder(self):
        def _load():
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        return self._lazy_load("skill_encoder", _load)

    def get_classifier(self):
        def _load():
            from transformers import pipeline
            return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        return self._lazy_load("classifier", _load)

    def get_text_generator(self):
        def _load():
            from transformers import pipeline
            return pipeline("text2text-generation", model="google/flan-t5-base")
        return self._lazy_load("text_generator", _load)

    def get_question_generator(self):
        def _load():
            from transformers import pipeline
            return pipeline("text2text-generation", model="mrm8488/t5-base-finetuned-question-generation-ap")
        return self._lazy_load("question_generator", _load)

    def get_nlp(self):
        def _load():
            import spacy
            return spacy.load("en_core_web_sm")
        return self._lazy_load("nlp", _load)

    def get_summarizer(self):
        def _load():
            from transformers import pipeline
            return pipeline("summarization", model="facebook/bart-large-cnn")
        return self._lazy_load("summarizer", _load)

    @property
    def skill_encoder(self):
        return self.get_skill_encoder()

    @property
    def classifier(self):
        return self.get_classifier()

    @property
    def text_generator(self):
        return self.get_text_generator()

    @property
    def question_generator(self):
        return self.get_question_generator()

    @property
    def nlp(self):
        return self.get_nlp()

    @property
    def summarizer(self):
        return self.get_summarizer()

    def unload_all(self):
        self._models.clear()
        self._loaded = False
        print("ML models unloaded.")

    def is_loaded(self):
        return self._loaded
