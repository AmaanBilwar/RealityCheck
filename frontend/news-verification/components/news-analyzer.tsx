"use client"
import axios from "axios"
import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, LinkIcon, MessageSquare, AlertCircle, CheckCircle } from "lucide-react"
import AnalysisResults from "@/components/analysis-results"

// Helper function to validate URLs
const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch (error) {
    return false
  }
}

// Define types for streaming updates
interface UpdateMessage {
  status: 'starting' | 'processing' | 'completed' | 'error' | 'warning' | 'info' | 'done';
  message: string;
  analysis_id?: string;
  data?: any;
}

export default function NewsAnalyzer() {
  const [inputType, setInputType] = useState<"url" | "text">("url")
  const [inputValue, setInputValue] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [urlError, setUrlError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  
  // New state for streaming updates
  const [streamingUpdates, setStreamingUpdates] = useState<UpdateMessage[]>([])
  const [progress, setProgress] = useState<number>(0)
  const [currentStep, setCurrentStep] = useState<string>("")

  // Validate URL whenever input changes (only when type is URL)
  useEffect(() => {
    if (inputType === "url" && inputValue) {
      setUrlError(!isValidUrl(inputValue))
    } else {
      setUrlError(false)
    }
  }, [inputValue, inputType])

  const handleAnalyze = async () => {
    setErrorMessage(null)
    setStreamingUpdates([])
    setProgress(0)
    setCurrentStep("")
    
    if (!inputValue.trim()) return

    // Double-check URL validity if needed
    if (inputType === "url" && !isValidUrl(inputValue)) {
      setUrlError(true)
      return
    }

    setIsAnalyzing(true)
    setAnalysisComplete(false)

    try {
      if (inputType === "url") {
        // For URLs, use the traditional endpoint
        const response = await axios.post('http://localhost:8000/api/analyze_url', { url: inputValue })
        
        if (response.status !== 200) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`)
        }

        const data = response.data
        console.log(`Analysis results for ${inputType}:`, data.analysis)
        setAnalysisData(data.analysis)
        setAnalysisComplete(true)
      } else {
        // For text content, use the streaming endpoint
        const eventSource = new EventSource(`http://localhost:8000/api/factcheck/stream?article=${encodeURIComponent(inputValue)}`);
        
        eventSource.onmessage = (event) => {
          try {
            const update = JSON.parse(event.data) as UpdateMessage;
            console.log("Received update:", update);
            
            // Add to streaming updates
            setStreamingUpdates(prev => [...prev, update]);
            setCurrentStep(update.message);
            
            // Update progress based on updates
            if (update.status === 'processing') {
              if (update.data?.current_chunk && update.data?.total_chunks) {
                // If we have chunk information, use it for progress
                const percent = Math.round((update.data.current_chunk / update.data.total_chunks) * 80) + 10;
                setProgress(percent); // Start at 10%, max at 90%
              } else {
                // Otherwise increment progress by small steps
                setProgress(prev => Math.min(prev + 3, 90));
              }
            } else if (update.status === 'starting') {
              setProgress(5);
            }
            
            // Handle completion
            if (update.status === 'completed' && update.data?.result_data) {
              setAnalysisData(update.data.result_data);
              setAnalysisComplete(true);
              setProgress(100);
              eventSource.close();
            } else if (update.status === 'done') {
              setProgress(100);
              eventSource.close();
            }
          } catch (error) {
            console.error("Error parsing event data:", error);
          }
        };
        
        eventSource.onerror = (error) => {
          console.error("EventSource error:", error);
          setErrorMessage("Connection to the analysis stream failed.");
          eventSource.close();
          setIsAnalyzing(false);
        };
      }
    } catch (error: any) {
      console.error("Analysis failed:", error)
      setErrorMessage("Analysis failed. Please try again later.")
      setAnalysisData(null)
      setAnalysisComplete(false)
    } finally {
      // For URL input or errors, we'll set isAnalyzing to false
      // For streaming text analysis, this happens when the stream completes
      if (inputType === "url") {
        setIsAnalyzing(false);
      }
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Input</CardTitle>
          <CardDescription>Provide a news article URL or paste text content for analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs 
            value={inputType} 
            onValueChange={(v: string) => {
              setInputType(v as "url" | "text")
              setInputValue("")
              setUrlError(false)
              setStreamingUpdates([])
              setProgress(0)
              setCurrentStep("")
            }} 
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="url">Article URL</TabsTrigger>
              <TabsTrigger value="text">Text Content</TabsTrigger>
            </TabsList>
            <TabsContent value="url" className="mt-4">
              <div className="flex flex-col space-y-3">
                <div>
                  <Input
                    placeholder="https://example.com/news-article"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={isAnalyzing}
                    className={urlError ? "border-red-500 focus-visible:ring-red-500" : ""}
                  />
                  {urlError && (
                    <div className="flex items-center mt-1 text-red-500 text-sm">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      <span>Please enter a valid URL</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  <LinkIcon className="mr-2 h-4 w-4" />
                  Enter the full URL of the news article
                </div>
              </div>
            </TabsContent>
            <TabsContent value="text" className="mt-4">
              <div className="flex flex-col space-y-3">
                <Textarea
                  placeholder="Paste the article text or paragraph you want to analyze..."
                  className="min-h-[200px] resize-none"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={isAnalyzing}
                />
                <div className="flex items-center text-sm text-muted-foreground">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Paste the full text or a specific paragraph for detailed analysis
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <Button 
            onClick={handleAnalyze} 
            disabled={!inputValue.trim() || isAnalyzing || (inputType === "url" && urlError)} 
            className="w-full sm:w-auto"
          >
            {isAnalyzing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isAnalyzing ? "Analyzing..." : "Analyze Content"}
          </Button>
          {errorMessage && (
            <p className="text-center text-red-500 text-sm">{errorMessage}</p>
          )}
        </CardFooter>
      </Card>

      {isAnalyzing && (
        <Card className="border border-muted/50">
          <CardContent className="pt-6">
            {inputType === "url" ? (
              <div className="flex flex-col items-center justify-center space-y-4 py-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <div className="text-center">
                  <p className="font-medium">Processing your article URL</p>
                  <p className="text-sm text-muted-foreground">
                    Our AI agents are fetching and analyzing the article...
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Progress bar for text analysis */}
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary rounded-full transition-all duration-300 ease-in-out"
                    style={{ width: `${progress}%` }} 
                  />
                </div>
                
                <div className="text-center mb-4">
                  <p className="font-medium">{currentStep || "Processing your text content"}</p>
                  <p className="text-sm text-muted-foreground">
                    {progress < 100 
                      ? "Our AI agents are analyzing the information..." 
                      : "Analysis complete!"}
                  </p>
                </div>
                
                {/* Recent updates display */}
                <div className="mt-6 space-y-2 max-h-60 overflow-y-auto border rounded-md p-3">
                  {streamingUpdates.slice(-5).map((update, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-sm p-1">
                      {update.status === 'error' || update.status === 'warning' ? (
                        <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                      ) : update.status === 'completed' || update.status === 'done' ? (
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      ) : (
                        <Loader2 className="h-4 w-4 text-primary animate-spin mt-0.5 flex-shrink-0" />
                      )}
                      <span>{update.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {analysisComplete && analysisData && (
        <AnalysisResults data={analysisData} />
      )}
    </div>
  )
}