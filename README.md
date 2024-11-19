# 📚 Multimodal Conversational Assistant for Product Search and Customer Support

A powerful conversational assistant that combines text, images, and natural language understanding to streamline product search and enhance customer experience.

## ✨ Key Features
- **Multimodal Interaction**: Combines text and image data for seamless product searches.
- **BigQuery Integration**: Efficiently fetches and processes product information from a robust database.
- **Custom Conversational Flow**: Allows dynamic and contextual conversations for a personalized user experience.
- **Streamlit UI**: Provides an interactive web interface for easy deployment and usage.

## 📂 Project Structure
datahub_st/ 
├── img/ # Directory to store project-related images 
│ └── cofares_logo.jpg # Cofares logo 
├── src/ # Source code of the project 
│ ├── authenticate.py # Script for authentication 
│ ├── background.py # Handles background tasks 
│ ├── bq_loader.py # Loads data from BigQuery 
│ ├── config.py # Configuration for Vector Search and other parameters 
│ ├── search.py # Search and retrieval functionalities 
│ ├── app.py # Main application built with Streamlit 
├── dockerfile # Docker image build configuration 
├── requirements.txt # Project dependencies 
├── README.md # Project documentation


## ⚙️ Setup and Installation

### Prerequisites
1. **Google Cloud SDK**  
    - Download and install Google Cloud SDK.
    ```bash
    # Authenticate your gcloud environment  
    gcloud auth login  
    
    # Set your project  
    gcloud config set project <PROJECT_ID>  
    ```
2. **Python Environment**  
    Ensure Python 3.10+ is installed.

### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/racaro/datahub_cofares.git 
    cd datahub_st 
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt 
    ```

3. Run the Streamlit app:
    ```bash
    streamlit run app.py  
    ```

## 🛠️ How It Works
1. **User Input**: The assistant accepts queries in natural language.
2. **Data Retrieval**: Uses BigQuery to fetch relevant product data based on user input.
3. **Vector Search**: Enhances search accuracy with semantic understanding.
4. **Dynamic Response**: Presents results as text, along with product images.

## 📊 Tech Stack
- **Backend**: Python, LangChain
- **Frontend**: Streamlit
- **Database**: Google BigQuery
- **Cloud**: Google Cloud Platform

## 🌐 Collaborators
- **Pau Garcia** (@Paugb01)
- **David Gonzalez** (@Dgasensi)
- **Carlos Buenrostro** (@cbuenrostrovalverde)
- **Raúl Carrasco** (@racaro)

## 🎨 Visual Workflow
1. User submits a query or uploads an image.
2. System processes input through BigQuery and Vector Search.
3. Results are dynamically displayed in the Streamlit interface.
