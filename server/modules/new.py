def newPrompt(number):
    prompt = f"""
    Extract structured content from the provided PDF for **MAIN QUESTION {number}** while preserving the order of elements as they appear in the document. The extracted content should follow these rules and schema:
    **GENERAL RULES**
    - Each main_question, question, and sub-question consists of a number and a content_flow array.
    - The JSON output must follow this format:
        - main_questions → Top-level questions numbered "1", "2", "3", etc.
        - questions → Sub-questions numbered "1(a)", "2(b)", "3(c)", etc.
        - sub_questions → Nested sub-questions numbered "1(a)(i)", "2(b)(ii)", etc.
    - Every main_question must have questions.
    - Not every question has sub_questions.
    - Extract marks and add its key to their related questions/sub_questions.
    - Every main_question, question, sub_question has a content_flow key.
    - The content_flow array can contain any of the following in any order, **depending on how they appear in the PDF**:
        - "text": Contains question descriptions and instructions (in english and malay, segregated by “english” and “malay” keys respectively. DO NOT MIX UP THE LANGUAGES)
        - "diagram": Represents figures, charts, or illustrations.
        - "table": Represents tabular data extracted from the document.
        - "row": A two-column layout for side-by-side diagrams or elements.
        - "question": Marks a question reference. (Only for content_flow array under main_question, *will be multiple according to PDF*)
        - "sub_question": Marks a sub_question reference. (Only for content_flow array under question, *will be multiple according to PDF*)
        - “answer_space”: Represents the space given for writing down answers.
    - Ensure the structure remains hierarchical:
        - Main questions (main_questions) should be nested under the top-level JSON object.
        - Questions are visually indented under their respective main_questions in the PDF; so the Questions (questions) array should be nested under their respective main_questions.
        - Sub-questions are visually indented under their respective questions in the PDF; so the Sub-Questions (sub_questions) array should be nested under their respective questions, if applicable. (For questions that do not have sub_questions, do not add unnecessary sub_questions array)
        - Answer spaces (answer_space) should follow their related questions.
        - Maintain the original order of elements as they appear in the PDF.

    **GENERAL SCHEMA**
    - main_questions: An array containing main question objects.
    - Each main_question object has:
        - number: A string representing the main question number (e.g., "1", "2").
        - content_flow: An array that dictates the order of content within the main question. If the content_flow contains {{"type": "questions"}}, this means sub questions will follow.
        - questions: An array containing question objects.
    - General schema for a main question object:
    ```json
    {{
        "main_questions": [
            {{
                "number": "<1 | 2 | 3 | etc.>",
                "content_flow": [
                    {{
                        "type": "text",
                        "text": {{
                            "malay": "<Text in Malay ONLY>",
                            "english": "<Text in English ONLY>"
                        }}
                    }},
                    {{
                        "type": "diagram",
                        "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                        "page": "<Page Number>"
                    }},
                    {{
                        "type": "row",
                        "layout": "2-columns",
                        "items": [
                            {{
                                "type": "diagram",
                                "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                                "page": "<Page Number A>"
                            }},
                            {{
                                "type": "diagram",
                                "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                                "page": "<Page Number B>"
                            }},
                        ]
                    }},
                    {{
                        "type": "table",
                        "number": "<Table Number>",
                        "page": "<Page Number>"
                    }},
                    {{
                        "type": "questions"
                    }}
                ],
                "questions": [
                    {{
                        "number": "<1(a) | 1(b) | 2(a) | etc.>",
                        "marks": "<1 | 2 | 3 | etc.>",
                        "content_flow": [
                            {{
                                "type": "text",
                                "text": {{
                                    "malay": "<Text in Malay>",
                                    "english": "<Text in English>"
                                }}
                            }},
                            {{
                                "type": "answer_space",
                                "format": "<multiple-choice | line | blank-space>",
                                "lines": "<Number of Lines>",
                                "options": [
                                    {{
                                        "malay": "<Option in Malay ONLY>",
                                        "english": "<Option in English ONLY>"
                                    }}
                                ]
                            }},
                            {{
                                "type": "sub_questions"
                            }}
                        ],
                        "sub_questions": [
                            {{
                                "number": "<1(a)(i) | 1(b)(ii) | 2(c)(i) | etc.>",
                                "marks": "<1 | 2 | 3 | etc.>",
                                "content_flow": [
                                    {{
                                        "type": "text",
                                        "text": {{
                                            "malay": "<Text in Malay ONLY>",
                                            "english": "<Text in English ONLY>"
                                        }}
                                    }},
                                    {{
                                        "type": "answer_space",
                                        "format": "<multiple-choice | line | blank-space>",
                                        "lines": "<Number of Lines>"
                                    }}
                                ]
                            }}
                        ]
                    }}
                ]
            }}
        ]
    }}
    ```

    **CONTENT FLOW ELEMENTS**
    - **Text**
        - **Strictly separate the text into 'malay' and 'english' keys.**
        - Use the following rules for language identification:
            - Text that is *italicized* is considered English.
            - Text that is not italicized is considered Malay.
        - **If there is ANY English text present, it MUST be placed in the 'english' key. If there is ANY Malay text present, it MUST be placed in the 'malay' key.**
        - **ABSOLUTELY DO NOT LEAVE THE 'malay' OR 'english' KEYS WITH EMPTY STRINGS OR NULL.**
        - **Do not translate or explain any of the text. Simply extract and separate.**
        - **If multiple lines of text are in the SAME language and appear consecutively, treat them as a SINGLE block of text for that language.**
        - Example OF *CORRECT* JSON object:
        ```json
        {{
            "type": "text",
            "text": {{
                "malay": "Apakah kesan negatif penggunaan tenaga hidroelektrik?",
                "english": "What are the negative impacts of using hydroelectric energy?"
            }}
        }}
        ````

        - Example OF *INCORRECT* JSON object **(STRICTY DO NOT DO THIS)**:
        ```json
        {{
            "type": "text",
            "text": {{
                "malay": "Apakah maksud imej maya?\n*What is meant by virtual image?*",
                "english": null
            }}
        }},
        {{
            "text": {{
                "malay": "Tandakan (√) bagi jawapan yang betul dalam kotak yang disediakan.\n*Tick (1) the correct answer in the box provided.*",
                "english": null
            }},
            "type": "text"
        }}
        ```         

    - **Diagram**
        - Represents figures, charts, or illustrations.
        - Only extract the diagram number and its PDF page number of appearance.
        - Will have a diagram number right below the diagram.
        - Typically has a text object before it that names and describes the diagram.
    - Example JSON object:
    ```json
    {{
        "type": "diagram",
        "number": "2.1",
        "page": "5"
    }}
    ```

    - **Table**
        - Represents tabular data extracted from the document.
        - Only extract the table number and its PDF page number of appearance.
        - Will have a table number right below the table.
        - Typically has a text object before it that names and describes the table.
    - Example JSON object:
    ```json
    {{
        "type": "table",
        "number": "1",
        "page": "3"
    }}
    ```

    - Row
        - A two-column layout for side-by-side diagrams or elements.
        - Extract the layout type and the items within the row.
        - Example JSON object:
    ```json
    {{
        "type": "row",
        "layout": "2-columns",
        "items": [
            {{
                "type": "diagram",
                "number": "1.1",
                "page": "2"
            }},
            {{
                "type": "diagram",
                "number": "1.2",
                "page": "2"
            }}
        ]
    }}
    ```

    - **Question**
        - Marks a question reference inside a main_question's "content_flow" array.
        - Numbered "1(a)", "2(b)", "3(c)", etc in the PDF.
        - Each question object has:
            - number: A string representing the question number (e.g., "1(a)", "2(b)").
            - marks: A string representing the marks allocated to the question.
            - content_flow: An array that dictates the order of content within the question.
        - Example JSON object inside a main_question's "content_flow" and "questions" array:
    ```json
    "main_questions": [
        {{
            "number": "1",
            "content_flow": [
                {{
                    "type": "questions"
                }}
            ],
            "questions": [
                {{
                    "number": "1(a)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Nyatakan Prinsip Keabadian Momentum?",
                                "english": "State the Principle of Conservation of Momentum?"
                            }}
                        }}
                    ]
                }},
                {{
                    "number": "1(b)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Nyatakan jenis perlanggaran yang terlibat dalam Rajah 1.",
                                "english": "State the type of collision involved in Diagram 1."
                            }}
                        }}
                    ]
                }}
            ]
        }}
    ]
    ```

    - **Sub-Question**
        - Marks a sub_question reference inside a question's "content_flow" array.
        - Numbered "(i)", "(ii)", "(iii)", etc in the PDF.
        - Each sub-question object has:
            - number: A string representing the sub-question number (e.g., "1(a)(i)", "2(b)(ii)").
            - marks: A string representing the marks allocated to the sub-question.
            - content_flow: An array that dictates the order of content within the sub-question.
        - Example JSON object inside a question's "content_flow" and "sub_questions" array:
    ```json
    "questions": [
        {{
        "number": "1(a)",
        "content_flow": [
                {{
                    "type": "sub_questions"
                }}
            ],
            "sub_questions": [
                {{
                    "number": "1(a)(i)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Lakarkan pesongan alur elektron dalam Rajah 1, jika nilai voltan lampau tinggi ( V.L.T ) ditingkatkan kepada 5000 V?",
                                "english": "Sketch the electron flow deflection in Diagram 1, if the value of the extra high tension ( EHT ) is increased to 5000 V?"
                            }}
                        }}
                    ]
                }},
                {{
                    "number": "1(a)(ii)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Beri satu sebab bagi jawapan anda di 1(c)(i).",
                                "english": "Give one reason for your answer in 1(c)(i)."
                            }}
                        }}
                    ]
                }},
            ]
        }}
    ]
    ```

    - **Answer Space**
        - Represents the space given for writing down answers.
        - Extract the format, number of lines, and options if applicable.
        - There are three formats: line, multiple-choice, and blank-space.
        a. Line
            - Illustrates the number of dotted-horizontal lines given for writing the answer.
            - Add a “line” key to the answer_space type element for line formats to represent the number of lines.
            - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "line",
            "lines": "<Number of lines>"
        }}
        ```

        b. Blank Space
            - Represents a blank space for answers.
            - A blank space is determined by visually identifying the space given from the question text and the marks allocator.
            - Typically for questions that involve calculations.
            - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "blank-space"
        }}
        ```

        c. Multiple-Choice
        - Represents a multiple-choice question that requires the user to select/tick the correct answer from a set of predetermined options.
        - Add an "options" key to represent the predetermined options.
        - Extract the options in both Malay and English.
        - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "multiple-choice",
            "options": [
                {{
                    "malay": "spektrum garis",
                    "english": "line spectrum"
                }},
                {{
                    "malay": "spektrum selanjar",
                    "english": "continuous spectrum"
                }}
            ]
        }}
        ```
    """
    return prompt

def newPrompt2(start, end):
    prompt = f"""
    Extract structured content from the provided PDF for **MAIN QUESTIONS {start} TO {end}** while preserving the order of elements as they appear in the document. The extracted content should follow these rules and schema:
    **GENERAL RULES**
    - Each main_question, question, and sub-question consists of a number and a content_flow array.
    - The JSON output must follow this format:
        - main_questions → Top-level questions numbered "1", "2", "3", etc.
        - questions → Sub-questions numbered "1(a)", "2(b)", "3(c)", etc.
        - sub_questions → Nested sub-questions numbered "1(a)(i)", "2(b)(ii)", etc.
    - Every main_question must have questions.
    - Not every question has sub_questions.
    - Extract marks and add its key to their related questions/sub_questions.
    - Every main_question, question, sub_question has a content_flow key.
    - The content_flow array can contain any of the following in any order, **depending on how they appear in the PDF**:
        - "text": Contains question descriptions and instructions (in english and malay, segregated by “english” and “malay” keys respectively. DO NOT MIX UP THE LANGUAGES)
        - "diagram": Represents figures, charts, or illustrations.
        - "table": Represents tabular data extracted from the document.
        - "row": A two-column layout for side-by-side diagrams or elements.
        - "question": Marks a question reference. (Only for content_flow array under main_question, *will be multiple according to PDF*)
        - "sub_question": Marks a sub_question reference. (Only for content_flow array under question, *will be multiple according to PDF*)
        - “answer_space”: Represents the space given for writing down answers.
    - Ensure the structure remains hierarchical:
        - Main questions (main_questions) should be nested under the top-level JSON object.
        - Questions are visually indented under their respective main_questions in the PDF; so the Questions (questions) array should be nested under their respective main_questions.
        - Sub-questions are visually indented under their respective questions in the PDF; so the Sub-Questions (sub_questions) array should be nested under their respective questions, if applicable. (For questions that do not have sub_questions, do not add unnecessary sub_questions array)
        - Answer spaces (answer_space) should follow their related questions.
        - Maintain the original order of elements as they appear in the PDF.

    **GENERAL SCHEMA**
    - main_questions: An array containing main question objects.
    - Each main_question object has:
        - number: A string representing the main question number (e.g., "1", "2").
        - content_flow: An array that dictates the order of content within the main question. If the content_flow contains {{"type": "questions"}}, this means sub questions will follow.
        - questions: An array containing question objects.
    - General schema for a main question object:
    ```json
    {{
        "main_questions": [
            {{
                "number": "<1 | 2 | 3 | etc.>",
                "content_flow": [
                    {{
                        "type": "text",
                        "text": {{
                            "malay": "<Text in Malay ONLY>",
                            "english": "<Text in English ONLY>"
                        }}
                    }},
                    {{
                        "type": "diagram",
                        "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                        "page": "<Page Number>"
                    }},
                    {{
                        "type": "row",
                        "layout": "2-columns",
                        "items": [
                            {{
                                "type": "diagram",
                                "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                                "page": "<Page Number A>"
                            }},
                            {{
                                "type": "diagram",
                                "number": "<1 | 1.1 | 1.2 | 2 | etc.>",
                                "page": "<Page Number B>"
                            }},
                        ]
                    }},
                    {{
                        "type": "table",
                        "number": "<Table Number>",
                        "page": "<Page Number>"
                    }},
                    {{
                        "type": "questions"
                    }}
                ],
                "questions": [
                    {{
                        "number": "<1(a) | 1(b) | 2(a) | etc.>",
                        "marks": "<1 | 2 | 3 | etc.>",
                        "content_flow": [
                            {{
                                "type": "text",
                                "text": {{
                                    "malay": "<Text in Malay>",
                                    "english": "<Text in English>"
                                }}
                            }},
                            {{
                                "type": "answer_space",
                                "format": "<multiple-choice | line | blank-space>",
                                "lines": "<Number of Lines>",
                                "options": [
                                    {{
                                        "malay": "<Option in Malay ONLY>",
                                        "english": "<Option in English ONLY>"
                                    }}
                                ]
                            }},
                            {{
                                "type": "sub_questions"
                            }}
                        ],
                        "sub_questions": [
                            {{
                                "number": "<1(a)(i) | 1(b)(ii) | 2(c)(i) | etc.>",
                                "marks": "<1 | 2 | 3 | etc.>",
                                "content_flow": [
                                    {{
                                        "type": "text",
                                        "text": {{
                                            "malay": "<Text in Malay ONLY>",
                                            "english": "<Text in English ONLY>"
                                        }}
                                    }},
                                    {{
                                        "type": "answer_space",
                                        "format": "<multiple-choice | line | blank-space>",
                                        "lines": "<Number of Lines>"
                                    }}
                                ]
                            }}
                        ]
                    }}
                ]
            }}
        ]
    }}
    ```

    **CONTENT FLOW ELEMENTS**
    - **Text**
        - **Strictly separate the text into 'malay' and 'english' keys.**
        - Use the following rules for language identification:
            - Text that is *italicized* is considered English.
            - Text that is not italicized is considered Malay.
        - **If there is ANY English text present, it MUST be placed in the 'english' key. If there is ANY Malay text present, it MUST be placed in the 'malay' key.**
        - **ABSOLUTELY DO NOT LEAVE THE 'malay' OR 'english' KEYS WITH EMPTY STRINGS OR NULL.**
        - **Do not translate or explain any of the text. Simply extract and separate.**
        - **If multiple lines of text are in the SAME language and appear consecutively, treat them as a SINGLE block of text for that language.**
        - Example OF *CORRECT* JSON object:
        ```json
        {{
            "type": "text",
            "text": {{
                "malay": "Apakah kesan negatif penggunaan tenaga hidroelektrik?",
                "english": "What are the negative impacts of using hydroelectric energy?"
            }}
        }}
        ````

        - Example OF *INCORRECT* JSON object **(STRICTY DO NOT DO THIS)**:
        ```json
        {{
            "type": "text",
            "text": {{
                "malay": "Apakah maksud imej maya?\n*What is meant by virtual image?*",
                "english": null
            }}
        }},
        {{
            "text": {{
                "malay": "Tandakan (√) bagi jawapan yang betul dalam kotak yang disediakan.\n*Tick (1) the correct answer in the box provided.*",
                "english": null
            }},
            "type": "text"
        }}
        ```         

    - **Diagram**
        - Represents figures, charts, or illustrations.
        - Only extract the diagram number and its PDF page number of appearance.
        - Will have a diagram number right below the diagram.
        - Typically has a text object before it that names and describes the diagram.
    - Example JSON object:
    ```json
    {{
        "type": "diagram",
        "number": "2.1",
        "page": "5"
    }}
    ```

    - **Table**
        - Represents tabular data extracted from the document.
        - Only extract the table number and its PDF page number of appearance.
        - Will have a table number right below the table.
        - Typically has a text object before it that names and describes the table.
    - Example JSON object:
    ```json
    {{
        "type": "table",
        "number": "1",
        "page": "3"
    }}
    ```

    - Row
        - A two-column layout for side-by-side diagrams or elements.
        - Extract the layout type and the items within the row.
        - Example JSON object:
    ```json
    {{
        "type": "row",
        "layout": "2-columns",
        "items": [
            {{
                "type": "diagram",
                "number": "1.1",
                "page": "2"
            }},
            {{
                "type": "diagram",
                "number": "1.2",
                "page": "2"
            }}
        ]
    }}
    ```

    - **Question**
        - Marks a question reference inside a main_question's "content_flow" array.
        - Numbered "1(a)", "2(b)", "3(c)", etc in the PDF.
        - Each question object has:
            - number: A string representing the question number (e.g., "1(a)", "2(b)").
            - marks: A string representing the marks allocated to the question.
            - content_flow: An array that dictates the order of content within the question.
        - Example JSON object inside a main_question's "content_flow" and "questions" array:
    ```json
    "main_questions": [
        {{
            "number": "1",
            "content_flow": [
                {{
                    "type": "questions"
                }}
            ],
            "questions": [
                {{
                    "number": "1(a)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Nyatakan Prinsip Keabadian Momentum?",
                                "english": "State the Principle of Conservation of Momentum?"
                            }}
                        }}
                    ]
                }},
                {{
                    "number": "1(b)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Nyatakan jenis perlanggaran yang terlibat dalam Rajah 1.",
                                "english": "State the type of collision involved in Diagram 1."
                            }}
                        }}
                    ]
                }}
            ]
        }}
    ]
    ```

    - **Sub-Question**
        - Marks a sub_question reference inside a question's "content_flow" array.
        - Numbered "(i)", "(ii)", "(iii)", etc in the PDF.
        - Each sub-question object has:
            - number: A string representing the sub-question number (e.g., "1(a)(i)", "2(b)(ii)").
            - marks: A string representing the marks allocated to the sub-question.
            - content_flow: An array that dictates the order of content within the sub-question.
        - Example JSON object inside a question's "content_flow" and "sub_questions" array:
    ```json
    "questions": [
        {{
        "number": "1(a)",
        "content_flow": [
                {{
                    "type": "sub_questions"
                }}
            ],
            "sub_questions": [
                {{
                    "number": "1(a)(i)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Lakarkan pesongan alur elektron dalam Rajah 1, jika nilai voltan lampau tinggi ( V.L.T ) ditingkatkan kepada 5000 V?",
                                "english": "Sketch the electron flow deflection in Diagram 1, if the value of the extra high tension ( EHT ) is increased to 5000 V?"
                            }}
                        }}
                    ]
                }},
                {{
                    "number": "1(a)(ii)",
                    "marks": "1",
                    "content_flow": [
                        {{
                            "type": "text",
                            "text": {{
                                "malay": "Beri satu sebab bagi jawapan anda di 1(c)(i).",
                                "english": "Give one reason for your answer in 1(c)(i)."
                            }}
                        }}
                    ]
                }},
            ]
        }}
    ]
    ```

    - **Answer Space**
        - Represents the space given for writing down answers.
        - Extract the format, number of lines, and options if applicable.
        - There are three formats: line, multiple-choice, and blank-space.
        a. Line
            - Illustrates the number of dotted-horizontal lines given for writing the answer.
            - Add a “line” key to the answer_space type element for line formats to represent the number of lines.
            - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "line",
            "lines": "<Number of lines>"
        }}
        ```

        b. Blank Space
            - Represents a blank space for answers.
            - A blank space is determined by visually identifying the space given from the question text and the marks allocator.
            - Typically for questions that involve calculations.
            - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "blank-space"
        }}
        ```

        c. Multiple-Choice
        - Represents a multiple-choice question that requires the user to select/tick the correct answer from a set of predetermined options.
        - Add an "options" key to represent the predetermined options.
        - Extract the options in both Malay and English.
        - Example JSON object:
        ```json
        {{
            "type": "answer_space",
            "format": "multiple-choice",
            "options": [
                {{
                    "malay": "spektrum garis",
                    "english": "line spectrum"
                }},
                {{
                    "malay": "spektrum selanjar",
                    "english": "continuous spectrum"
                }}
            ]
        }}
        ```
    """
    return prompt