'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import axios from 'axios'
import { motion } from 'framer-motion'
import { SidebarProvider } from "@/components/ui/sidebar"
import AppSidebar from "@/components/app-sidebar"
import { ThemeProvider } from "@/components/theme-provider"
import { Share2, RefreshCw, Expand, AlertCircle } from "lucide-react"
import EntityCloud from "@/components/EntityCloud"
// Define interface for thread data
interface ThreadData {
  _id: string;
  topic: string;
  articles: [{
    title: string;
    source: string;
    date: string;
    snippet: string;
    content: string;
    url: string;
  }];
  factual_accuracy?: number;
  bias_analysis?: string;
  timestamp: string;
  // Add other properties as needed
}
// Add this interface to your existing interfaces
interface NEREntity {
  name: string;
  sentiment: string | number; // "positive"/"negative" or numeric value
  type: string;
}

// Simple gauge component to replace the missing one
const SimpleGauge = ({ value = 0, size = "large" }) => {
  const strokeWidth = 8;
  const radius = size === "large" ? 40 : 30;
  const circumference = 2 * Math.PI * radius;
  const progress = (value / 100) * circumference;
  
  return (
    <div className="flex flex-col items-center justify-center">
      <svg width={radius * 2 + strokeWidth} height={radius * 2 + strokeWidth} className="transform -rotate-90">
        <circle
          cx={radius + strokeWidth/2}
          cy={radius + strokeWidth/2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.2"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={radius + strokeWidth/2}
          cy={radius + strokeWidth/2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          className="text-primary transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute text-2xl font-bold">{value}%</div>
    </div>
  );
};

export default function ThreadPage() {
  const params = useParams()
  const threadId = params.threadId as string
  const [threadData, setThreadData] = useState<ThreadData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [NER, setNER] = useState<any>([{'name': 'Jackson', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
    {'name': 'Trump', 'type': 'PERSON', 'sentiment': 'NEGATIVE'},
    {'name': 'Dellinger', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
    {'name': 'last year', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
    {'name': 'Saturday', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
    {'name': 'last month', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
    {'name': 'Office of Special Counsel',
    'type': 'ORGANIZATION',
    'sentiment': 'NEUTRAL'},
    {'name': 'Congress', 'type': 'ORGANIZATION', 'sentiment': 'NEUTRAL'},
    {'name': '67-page', 'type': 'QUANTITY', 'sentiment': 'NEUTRAL'},
    {'name': 'Supreme Court', 'type': 'ORGANIZATION', 'sentiment': 'NEUTRAL'},
    {'name': 'Amy Berman Jackson', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
    {'name': 'Justice Department',
    'type': 'ORGANIZATION',
    'sentiment': 'NEUTRAL'},
    {'name': 'more than four decades',
    'type': 'QUANTITY',
    'sentiment': 'NEUTRAL'},
    {'name': 'five-year term', 'type': 'QUANTITY', 'sentiment': 'NEUTRAL'},
    {'name': 'President Donald Trump', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
    {'name': 'Hampton Dellinger', 'type': 'PERSON', 'sentiment': 'NEUTRAL'}])
  

  useEffect(() => {
    const fetchThreadData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        console.log("Fetching thread data from API for ID:", threadId)
        const response = await axios.get(`http://localhost:8000/api/thread/${threadId}`)
        
        if (response.data) {
          // Log the entire response to inspect structure
          console.log("Full API response:", response.data)
          
          setThreadData(response.data.Thread_Data)
          
          // Log NER data specifically and check if it exists
          // Inside your useEffect function, change this part:
          if (response.data.NER) {
            console.log("NER data exists:", response.data.NER)
            setNER(response.data.NER) // Add this line to update the state with API data
          } else {
            console.warn("No NER data in response")
            setNER([]) // Set empty array instead of null
          }
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
        <div className="flex h-screen relative">
          <AppSidebar />
          
          <main className="flex-1 p-6 overflow-auto relative">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="relative w-24 h-24"
                >
                  <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </motion.div>
                <p className="text-muted-foreground">Analyzing geopolitical discourse...</p>
              </div>
            ) : error ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center h-full gap-4"
              >
                <div className="p-4 rounded-full bg-red-100 dark:bg-red-900/30">
                  <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
                </div>
                <h2 className="text-xl font-semibold">Error Loading Data</h2>
                <p className="text-muted-foreground text-center max-w-md">{error}</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="flex items-center gap-2 mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
              </motion.div>
            ) : threadData.length > 0 ? (
              <div className="max-w-5xl mx-auto space-y-8 relative">
                {/* Animated Hero Section */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 p-8"
                >
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(var(--primary)/0.1),transparent)]" />
                  <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                    {threadData[0].topic}
                  </h1>
                  <div className="mt-4 flex gap-4">
                    <div className="flex items-center gap-2 bg-background/50 backdrop-blur px-4 py-2 rounded-full">
                      <span className="text-sm text-muted-foreground">Processed:</span>
                      <span className="font-medium">{new Date(threadData[0].timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>
                </motion.div>

                {/* Summary Card with 3D Effect */}
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="group relative bg-card rounded-xl border shadow-xl p-6 transition-all duration-300 hover:shadow-2xl"
                >
                  <div className="absolute inset-0 rounded-xl bg-[radial-gradient(circle_at_top_left,_var(--tw-gradient-stops))] from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Key Insights
                    </span>
                  </h2>
                  <div className="text-lg leading-relaxed whitespace-pre-wrap">
                    <div className="space-y-4">
                      {threadData[0].articles.map((article, index) => (
                        <motion.div 
                          key={index}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="bg-card/50 border rounded-lg p-4 hover:shadow-md transition-shadow"
                        >
                          <h3 className="font-bold text-lg mb-1">{article.title}</h3>
                          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mb-2">
                            <span>{article.source}</span>
                            <span>•</span>
                            <span>{new Date(article.date).toLocaleDateString()}</span>
                          </div>
                          <p className="text-muted-foreground mb-3">{article.snippet}</p>
                          <details className="group">
                            <summary className="cursor-pointer text-sm text-primary font-medium hover:underline">
                              Read full content
                            </summary>
                            <div className="mt-3 text-sm border-t pt-3 whitespace-pre-wrap">
                              {article.content}
                            </div>
                          </details>
                          {article.url && (
                            <a 
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer" 
                              className="text-xs text-primary hover:underline mt-2 inline-block"
                            >
                              View original source
                            </a>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
                <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-card rounded-xl border shadow-sm p-6"
          >
            <h3 className="text-xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Key Entities & Sentiment
            </h3>
            
            {NER ? (
              <>
                    <div className="mb-4 text-sm text-muted-foreground">
                      Found {NER.length} entities
                    </div>
                    <EntityCloud entities={NER} />
                  </>
                ) : (
                  <div className="flex items-center justify-center h-32 text-muted-foreground">
                    No entity data available
                  </div>
            )}
          </motion.div>

                {/* Data Visualization Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Factual Accuracy Gauge */}
                  <div className="bg-card p-6 rounded-xl border shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">Factual Confidence</h3>
                    <div className="relative w-full h-32 flex items-center justify-center">
                      <SimpleGauge 
                        value={threadData[0].factual_accuracy || 43}
                        size="large"
                      />
                      <div className="absolute bottom-0 text-sm text-muted-foreground">
                        AI Confidence Score
                      </div>
                    </div>
                  </div>

                  {/* Bias Analysis Interactive Chart */}
                  <div className="bg-card p-6 rounded-xl border shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">Bias Spectrum</h3>
                    <div className="relative h-32">
                      <div className="absolute inset-x-4 top-1/2 h-1 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-full" />
                      <motion.div
                        initial={{ x: '-50%' }}
                        animate={{
                          x: `${(parseInt(threadData[0].bias_analysis || '0') / 100) * 80}%`
                        }}
                        className="absolute top-1/2 w-8 h-8 bg-background border-2 border-primary rounded-full shadow-lg"
                        style={{ left: '10%' }}
                      />
                      <div className="absolute bottom-0 inset-x-0 flex justify-between text-sm">
                        <span className="text-green-600">Neutral</span>
                        <span className="text-red-600">Biased</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating Action Buttons */}
                <div className="fixed bottom-8 right-8 flex gap-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-3 rounded-full bg-primary text-primary-foreground shadow-lg"
                  >
                    <Share2 className="w-5 h-5" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-3 rounded-full bg-primary text-primary-foreground shadow-lg"
                  >
                    <Expand className="w-5 h-5" />
                  </motion.button>
                </div>
              </div>
            ) : (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center h-full gap-4"
              >
                <div className="p-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30">
                  <AlertCircle className="w-10 h-10 text-yellow-600 dark:text-yellow-400" />
                </div>
                <h2 className="text-xl font-semibold">No Data Found</h2>
                <p className="text-muted-foreground text-center max-w-md">
                  We couldn't find any thread data with the specified ID. Please check the ID and try again.
                </p>
                <button 
                  onClick={() => window.history.back()}
                  className="flex items-center gap-2 mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Go Back
                </button>
              </motion.div>
            )}
          </main>
        </div>
      </SidebarProvider>
    </ThemeProvider>
  )
}