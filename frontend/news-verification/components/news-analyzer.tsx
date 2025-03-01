"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, LinkIcon, MessageSquare } from "lucide-react"
import AnalysisResults from "@/components/analysis-results"

export default function NewsAnalyzer() {
  const [inputType, setInputType] = useState<"url" | "text">("url")
  const [inputValue, setInputValue] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisData, setAnalysisData] = useState<any>(null)

  const handleAnalyze = async () => {
    if (!inputValue.trim()) return

    setIsAnalyzing(true)
    setAnalysisComplete(false)

    try {
      // In a real implementation, this would call your backend API
      // that connects to the agents shown in the diagram
      await new Promise((resolve) => setTimeout(resolve, 2000)) // Simulate API call

      // Mock response data
      const mockData = {
        highlights: [
          { text: "The study found a 25% increase in renewable energy adoption.", sentiment: "positive" },
          { text: "Critics argue the methodology is flawed and results are overstated.", sentiment: "negative" },
          { text: "Government officials have not yet responded to the findings.", sentiment: "neutral" },
        ],
        overallSentiment: "mixed",
        relatedSources: [
          { title: "Similar study from Stanford University", url: "#", reliability: "high" },
          { title: "Contradicting report from Industry Association", url: "#", reliability: "medium" },
          { title: "Previous research on the same topic", url: "#", reliability: "high" },
        ],
        factChecks: [
          { claim: "25% increase in renewable energy", verdict: "Mostly True", source: "EnergyFact.org" },
          { claim: "Methodology is flawed", verdict: "Disputed", source: "ScienceCheck" },
        ],
      }

      setAnalysisData(mockData)
      setAnalysisComplete(true)
    } catch (error) {
      console.error("Analysis failed:", error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Input</CardTitle>
          <CardDescription>Provide a news article URL or paste text content for analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={inputType} onValueChange={(v) => setInputType(v as "url" | "text")} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="url">Article URL</TabsTrigger>
              <TabsTrigger value="text">Text Content</TabsTrigger>
            </TabsList>
            <TabsContent value="url" className="mt-4">
              <div className="flex flex-col space-y-4">
                <Input
                  placeholder="https://example.com/news-article"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={isAnalyzing}
                />
                <div className="flex items-center text-sm text-muted-foreground">
                  <LinkIcon className="mr-2 h-4 w-4" />
                  Enter the full URL of the news article you want to analyze
                </div>
              </div>
            </TabsContent>
            <TabsContent value="text" className="mt-4">
              <div className="flex flex-col space-y-4">
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
        <CardFooter>
          <Button onClick={handleAnalyze} disabled={!inputValue.trim() || isAnalyzing} className="w-full sm:w-auto">
            {isAnalyzing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isAnalyzing ? "Analyzing..." : "Analyze Content"}
          </Button>
        </CardFooter>
      </Card>

      {isAnalyzing && (
        <Card className="border border-muted/50">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-center">
                <p className="font-medium">Processing your content</p>
                <p className="text-sm text-muted-foreground">Our AI agents are analyzing the information...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {analysisComplete && analysisData && <AnalysisResults data={analysisData} />}
    </div>
  )
}

