from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.document_loaders.csv_loader import CSVLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
import os

from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env (especially openai api key)
api_key = os.getenv("GOOGLE_API_KEY")
# Create Google Palm LLM model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # or "gemini-1.5-flash-latest"
    google_api_key=api_key,
    temperature=0.3,
)
# # Initialize instructor embeddings using the Hugging Face model
embedding = HuggingFaceEmbeddings(
    model_name="hkunlp/instructor-large",
    encode_kwargs={"normalize_embeddings": True}
)
vectordb_file_path = "faiss_index"

def create_vector_db():
    # Load data from FAQ sheet
    loader = CSVLoader(file_path='faqs.csv', source_column="prompt")
    data = loader.load()

    # Create a FAISS instance for vector database from 'data'
    vectordb = FAISS.from_documents(documents=data,
                                    embedding=embedding)

    # Save vector database locally
    vectordb.save_local(vectordb_file_path)


def get_qa_chain():
    # Load the vector database from the local folder
    vectordb = FAISS.load_local(vectordb_file_path, embedding, allow_dangerous_deserialization=True)


    # Create a retriever for querying the vector database
    retriever = vectordb.as_retriever(score_threshold=0.7)

    prompt_template = """
You are a helpful assistant. Answer the user's question based on the context below.

- Rephrase and restructure the answer in your own words from "response" section in the source document
- Use natural, friendly language.
- Do not copy directly from the context unless necessary.
- If the answer is not found in the context, reply: "I'm not sure. Please email us at xyz@gmail.com."

CONTEXT: {context}

QUESTION: {question}
"""


    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain = RetrievalQA.from_chain_type(llm=llm,
                                        chain_type="stuff",
                                        retriever=retriever,
                                        input_key="query",
                                        return_source_documents=True,
                                        chain_type_kwargs={"prompt": PROMPT})

    return chain

if __name__ == "__main__":
    create_vector_db()
    chain = get_qa_chain()
    print(chain("Do you have javascript course?"))