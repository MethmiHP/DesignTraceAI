from .router import router

def __init__(self):
    self.preprocessor = Preprocessor()
    self.semantic_extractor = RuleBasedSemanticExtractor()
    self.responsibility_mapper = ResponsibilityMapper()
    self.database_context_builder = DatabaseContextBuilder()
    self.api_generator = BaselineAPIGenerator()
    self.openapi_builder = OpenAPIBuilder()
    self.validator = APIDesignValidator()
    self.refinement_engine = RefinementEngine()