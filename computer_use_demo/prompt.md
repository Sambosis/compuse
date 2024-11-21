# Your will be developing a vector database specialized for code.  There is a python file in the directory  c:/repo/code_tools/code_tools.py that contains a Library that can be used to scan and analyze code. 

You will be using the library to scan a code repository and extract information about the code.  You will then use that information to create a vector database.

The code stores a lot of metadata about the code, including function and method definitions, class definitions, dependencies, and more.

The vector database should be capable of storing and querying the metadata as well as the full code content.

You will be using pinecone to create the vector database and their is a .env file in the root of the project that contains your PINECONE_API_KEY.
This also contains a HUGGINGFACE_API_KEY which is for the embedding model.

One of the use cases of this will be to provide code context to give an LLM more information about the code to assist it in completing code and fixing errors. 

You will then use the vector database to answer questions about the code that is stored in the sample_data directory.

At anytime you can review the journal of the steps taken to create the vector database by opening the file:
C:\mygit\compuse\computer_use_demo\journal\journal.log



If you have any questions, instead of asking the user,please get an expert opinion.
    When you are done, please test the app to make sure it works. If it or any feature of it is not working, please fix it.

If you finish and it is all working, please ask for an expert opinion on additional features you could add.
