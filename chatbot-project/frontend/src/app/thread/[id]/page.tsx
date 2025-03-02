'use client'


import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import axios from 'axios'
import { SidebarProvider } from "@/components/ui/sidebar"
import AppSidebar from "@/components/app-sidebar"
import { ThemeProvider } from "@/components/theme-provider"

// Define interface for thread data
interface ThreadData {
  _id: string;
  topic: string;
  summary: string;
  factual_accuracy?: number;
  bias_analysis?: string;
  processed_date: string;
  // Add other properties as needed
}

export default function ThreadPage() {
  const params = useParams()
  const threadId = params.id as string
  const [threadData, setThreadData] = useState<ThreadData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchThreadData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // First try to get data from localStorage (if navigated from sidebar)
        const cachedData = localStorage.getItem('currentThreadData')
        if (cachedData) {
          const parsedData = JSON.parse(cachedData)
          setThreadData(parsedData)
          setLoading(false)
          console.log("Loaded thread data from cache:", parsedData)
          return
        }
        
        // If no cached data, fetch from API
        console.log("Fetching thread data from API for ID:", threadId)
        const response = await axios.get(`http://localhost:8000/api/thread/${threadId}`)
        
        if (response.data && response.data.Thread_Data) {
          setThreadData(response.data.Thread_Data)
          console.log("Fetched thread data from API:", response.data.Thread_Data)
        } else {
          throw new Error("No data found for this thread")
        }
      } catch (err) {
        console.error("Error fetching thread data:", err)
        setError("Failed to load thread data. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchThreadData()
  }, [threadId])

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <SidebarProvider defaultOpen={true}>
        <div className="flex h-screen">
          <AppSidebar />
          
          <main className="flex-1 p-6 overflow-auto">
            {loading ? (
              <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : error ? (
              <div className="text-center text-red-500">
                <p className="text-xl font-bold">Error</p>
                <p>{error}</p>
              </div>
            ) : threadData.length > 0 ? (
              <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold">{threadData[0].topic}</h1>
                
                <div className="bg-card rounded-lg border shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Summary</h2>
                  <p className="whitespace-pre-wrap">{threadData[0].summary}</p>
                </div>
                
                {/* Add more components to display other thread data */}
                {/* For example: factual accuracy, bias analysis, etc. */}
              </div>
            ) : (
              <div className="text-center">
                <p className="text-xl font-bold">No data found</p>
                <p className="text-muted-foreground">No data available for this thread.</p>
              </div>
            )}
          </main>
        </div>
      </SidebarProvider>
    </ThemeProvider>
  )
}