from ..utils.logger import get_logger

logger = get_logger(__name__)

class StoryAgent:
    def __init__(self, parser, retriever, writer):
        self.parser = parser
        self.retriever = retriever
        self.writer = writer
