# Chatbot Project

This project is a chatbot application built using Next.js for the frontend and FastAPI for the backend. The application allows users to interact with a chatbot by sending messages and receiving responses.

## Project Structure

```
chatbot-project
├── frontend
│   ├── public
│   │   └── favicon.ico
│   ├── src
│   │   ├── app
│   │   │   ├── api
│   │   │   │   └── route.ts
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components
│   │   │   ├── chat-input.tsx
│   │   │   ├── chat-message.tsx
│   │   │   ├── chat.tsx
│   │   │   └── ui
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       └── textarea.tsx
│   │   ├── lib
│   │   │   └── api.ts
│   │   ├── styles
│   │   │   └── globals.css
│   │   └── types
│   │       └── index.ts
│   ├── .env.local
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── backend
│   ├── app
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   └── models.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   └── chat_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── .gitignore
└── README.md
```

## Frontend

The frontend is built using Next.js and includes the following key components:

- **ChatInput**: A component for users to input messages.
- **ChatMessage**: A component to display individual chat messages.
- **Chat**: The main chat interface that combines ChatInput and ChatMessage.
- **API Integration**: The frontend communicates with the FastAPI backend through defined API routes.

### Installation

To get started with the frontend, navigate to the `frontend` directory and run:

```bash
npm install
```

Then, start the development server:

```bash
npm run dev
```

## Backend

The backend is built using FastAPI and includes the following key components:

- **Chat API**: Handles incoming messages and responses.
- **Models**: Defines the data models used in the application.
- **Services**: Contains the business logic for handling chat interactions.

### Installation

To set up the backend, navigate to the `backend` directory and install the required dependencies:

```bash
pip install -r requirements.txt
```

Then, run the FastAPI application:

```bash
uvicorn app.main:app --reload
```

## Environment Variables

Both the frontend and backend applications use environment variables for configuration. Make sure to set up the `.env` files in both directories with the necessary variables.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License.