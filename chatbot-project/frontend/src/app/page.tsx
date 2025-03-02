import Chat from "@/components/chat"

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-3xl font-bold mb-4">Chatbot Application</h1>
      <Chat />
    </main>
  )
}