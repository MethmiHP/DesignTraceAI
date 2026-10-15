# DesignTrace AI — NLP Annotation Guidelines

## 1. Purpose

This document defines the annotation rules for preparing the NLP concept extraction dataset used by the DesignTrace AI Database Design Module.

The dataset contains software requirements annotated with database-related entities, attributes, and actions.

The annotations will support the evaluation and possible fine-tuning of NLP models such as BERT, RoBERTa, and DeBERTa.

## 2. Annotation Labels

| Label | Meaning | Examples |
|---|---|---|
| ENTITY | A candidate database entity or object that may become a database table | patient, doctor, appointment, student, course |
| ATTRIBUTE | A property or field belonging to an entity | name, email, phone number, status, credits |
| ACTION | An operation or interaction described in a requirement | book, borrow, enroll, register, cancel |
| OTHER (O) | Words that do not represent an entity, attribute, or action | the, a, can, shall, with |

Only ENTITY, ATTRIBUTE, and ACTION spans are stored in the JSON annotations. All other words are implicitly labeled OTHER.

## 3. General Annotation Rules

1. Read the complete requirement before assigning labels.
2. Identify database-related entities, attributes, and actions.
3. Annotate the exact words appearing in the requirement.
4. Do not annotate words that are not present in the original text.
5. Use the correct character start and end positions.
6. Use singular or plural words exactly as written in the requirement.
7. Do not assign overlapping labels to the same text span.
8. Use the meaning of the word in its sentence to decide the label.
9. Do not automatically label every noun as an entity.
10. If an annotation is unclear, flag it for human review.

## 4. Entity Annotation Rules

An ENTITY represents a candidate database object that may require persistent storage.

Examples:

- "patient" → ENTITY
- "doctors" → ENTITY
- "appointment" → ENTITY
- "student" → ENTITY
- "course" → ENTITY
- "borrowing record" → ENTITY

Plural entities are annotated exactly as written.

Example:

"Doctors can view appointments."

- Doctors → ENTITY
- view → ACTION
- appointments → ENTITY

## 5. Attribute Annotation Rules

An ATTRIBUTE describes information stored about an entity.

Examples:

- "email" → ATTRIBUTE
- "phone number" → ATTRIBUTE
- "publication date" → ATTRIBUTE
- "course code" → ATTRIBUTE, when referring to the complete field
- "status" → ATTRIBUTE

Multi-word attributes should be annotated as one complete span when they represent a single field.

Example:

"The patient must provide an email and phone number."

- patient → ENTITY
- email → ATTRIBUTE
- phone number → ATTRIBUTE

## 6. Action Annotation Rules

An ACTION describes an operation involving database-related information.

Examples:

- "book" → ACTION
- "borrow" → ACTION
- "enroll" → ACTION
- "register" → ACTION
- "cancel" → ACTION
- "update" → ACTION

Example:

"A patient can book an appointment with a doctor."

- patient → ENTITY
- book → ACTION
- appointment → ENTITY
- doctor → ENTITY

## 7. Ambiguous Words

Some words can have different labels depending on context.

### Example 1: Book

"The member can borrow a book."

- member → ENTITY
- borrow → ACTION
- book → ENTITY

"The patient can book an appointment."

- patient → ENTITY
- book → ACTION
- appointment → ENTITY

### Example 2: Order

"The customer can place an order."

- customer → ENTITY
- place → ACTION
- order → ENTITY

### Example 3: Record

"The system shall store borrowing records."

- store → ACTION
- borrowing records → ENTITY

"The librarian can record a borrowing."

- record → ACTION
- borrowing → ENTITY

The label must be selected based on the meaning of the word in the requirement.

## 8. Character Position Rules

Each annotation must contain:

- text
- label
- start
- end

Character positions use zero-based indexing.

The start position is inclusive, and the end position is exclusive.

For example, in:

"A student can enroll in a course."

The word "student" starts at position 2 and ends at position 9.

The annotated text must exactly match:

`requirement_text[start:end]`

If the extracted substring does not match the annotation text, the annotation must be corrected.

## 9. Dataset Quality Review

Before using the dataset for model training:

1. Check that every requirement has a unique requirement ID.
2. Check that every annotation uses a valid label.
3. Check that character positions match the original text.
4. Check that annotation spans do not overlap.
5. Review ambiguous words and multi-word concepts.
6. Confirm that entities, attributes, and actions are labeled consistently.
7. Have a human reviewer verify and correct the AI-generated annotations.

## 10. Dataset Splitting

The reviewed dataset will be divided into:

- Training dataset — used for model fine-tuning.
- Validation dataset — used for model selection and tuning.
- Test dataset — used for final evaluation.

Requirements from the same project should remain in the same split to reduce data leakage.

The test dataset must not be used to modify annotation rules, tune models, or select the best model.

## 11. Evaluation

The NLP concept extraction models will be evaluated using:

- Precision
- Recall
- F1-score

Results should be calculated separately for ENTITY, ATTRIBUTE, and ACTION, as well as overall.

The rule-based extractor will serve as the initial baseline for comparison with fine-tuned NLP models.

## 12. Dataset Limitations

The initial 50-requirement dataset is a synthetic pilot dataset.

It is intended for testing annotation structure, data loading, validation, and early NLP experiments.

It must not be described as a human-verified gold-standard dataset until its annotations have been independently reviewed.

Additional requirements from diverse software projects will be needed for more reliable fine-tuning and evaluation.