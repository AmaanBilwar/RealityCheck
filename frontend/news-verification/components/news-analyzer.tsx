"use client"
import axios from "axios"
import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, LinkIcon, MessageSquare, AlertCircle } from "lucide-react"
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

export default function NewsAnalyzer() {
  const [inputType, setInputType] = useState<"url" | "text">("url")
  const [inputValue, setInputValue] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [urlError, setUrlError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

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
    if (!inputValue.trim()) return

    // Double-check URL validity if needed
    if (inputType === "url" && !isValidUrl(inputValue)) {
      setUrlError(true)
      return
    }

    setIsAnalyzing(true)
    setAnalysisComplete(false)

    try {
      let response;
      if (inputType === "url") {
        response = await axios.post('http://localhost:8000/api/analyze_url', { url: inputValue })
      } else {
        response = await axios.post('http://localhost:8000/api/news_input', { text: inputValue })
      }

      if (response.status !== 200) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`)
      }

      const data = response.data
      console.log(`Analysis results for ${inputType}:`, data.analysis)
      setAnalysisData(data.analysis)
      setAnalysisComplete(true)
    } catch (error: any) {
      console.error("Analysis failed:", error)
      setErrorMessage("Analysis failed. Please try again later.")
      setAnalysisData(null)
      setAnalysisComplete(false)
    } finally {
      setIsAnalyzing(false)
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
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-center">
                <p className="font-medium">
                  Processing your {inputType === "url" ? "article URL" : "text content"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {inputType === "url" 
                    ? "Our AI agents are fetching and analyzing the article..." 
                    : "Our AI agents are analyzing the information..."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {analysisComplete && analysisData && (
        <AnalysisResults data={analysisData} />
      )}
    </div>
  )
}
