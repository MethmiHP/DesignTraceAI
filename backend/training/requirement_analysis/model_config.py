#This gives us the three models:
#DistilBERT
#BERT-base
#RoBERTa-base

MODELS = {
    "distilbert": "distilbert-base-uncased",
    "bert": "bert-base-uncased",
    "roberta": "roberta-base",
}


TRAINING_CONFIG = {
    "test_size": 0.15,
    "validation_size": 0.15,
    "random_state": 42,
    "num_train_epochs": 3,
    "learning_rate": 2e-5,
    "batch_size": 8,
}