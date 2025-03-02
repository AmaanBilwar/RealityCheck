"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Minus,
  ExternalLink,
  AlertTriangle,
  CheckCircle,
  Info,
} from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"

interface AnalysisResultsProps {
  data: {
    highlights?: Array<{ text: string; sentiment: string }>;
    overallSentiment?: string;
    relatedSources?: Array<{ title: string; url: string; reliability: string }>;
    factChecks?: Array<{ claim: string; verdict: string; source: string }>;
  }
}

export default function AnalysisResults({ data }: AnalysisResultsProps) {
  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <ThumbsUp className="h-4 w-4 text-green-500" />
      case "negative":
        return <ThumbsDown className="h-4 w-4 text-red-500" />
      case "neutral":
      case "mixed":
      default:
        return <Minus className="h-4 w-4 text-yellow-500" />
    }
  }

  const getReliabilityBadge = (reliability: string) => {
    switch (reliability) {
      case "high":
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 hover:bg-green-50">
            High Reliability
          </Badge>
        )
      case "medium":
        return (
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">
            Medium Reliability
          </Badge>
        )
      case "low":
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 hover:bg-red-50">
            Low Reliability
          </Badge>
        )
      default:
        return <Badge variant="outline">Unknown Reliability</Badge>
    }
  }

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case "True":
      case "Mostly True":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">{verdict}</Badge>
      case "Partly True":
      case "Disputed":
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">{verdict}</Badge>
      case "False":
      case "Mostly False":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">{verdict}</Badge>
      default:
        return <Badge variant="outline">{verdict}</Badge>
    }
  }

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Positive</Badge>
      case "negative":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Negative</Badge>
      case "neutral":
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Neutral</Badge>
      case "mixed":
        return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">Mixed</Badge>
      default:
        return <Badge variant="outline">{sentiment}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            Analysis Results
            {data.overallSentiment && <span className="ml-2">{getSentimentBadge(data.overallSentiment)}</span>}
          </CardTitle>
          <CardDescription>Key insights and verification of the content</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="highlights" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="highlights">Key Highlights</TabsTrigger>
              <TabsTrigger value="sources">Related Sources</TabsTrigger>
              <TabsTrigger value="factcheck">Fact Checks</TabsTrigger>
            </TabsList>

            <TabsContent value="highlights" className="mt-4 space-y-4">
              {data.highlights && data.highlights.length > 0 ? (
                data.highlights.map((highlight, index) => (
                  <div key={index} className="rounded-lg border p-4">
                    <div className="flex items-start space-x-2">
                      <div className="mt-1">{getSentimentIcon(highlight.sentiment)}</div>
                      <div>
                        <p className="text-sm font-medium">{highlight.text}</p>
                        <div className="mt-2">{getSentimentBadge(highlight.sentiment)}</div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-muted-foreground">No highlights available</div>
              )}
            </TabsContent>

            <TabsContent value="sources" className="mt-4 space-y-4">
              {data.relatedSources && data.relatedSources.length > 0 ? (
                data.relatedSources.map((source, index) => (
                  <div key={index} className="rounded-lg border p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{source.title}</p>
                        <div className="mt-2">{getReliabilityBadge(source.reliability)}</div>
                      </div>
                      <Button variant="ghost" size="icon" asChild>
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4" />
                          <span className="sr-only">Open link</span>
                        </a>
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-muted-foreground">No related sources available</div>
              )}
            </TabsContent>

            <TabsContent value="factcheck" className="mt-4 space-y-4">
              {data.factChecks && data.factChecks.length > 0 ? (
                data.factChecks.map((check, index) => (
                  <div key={index} className="rounded-lg border p-4">
                    <div className="space-y-2">
                      <div className="flex items-start space-x-2">
                        {check.verdict.includes("True") ? (
                          <CheckCircle className="mt-0.5 h-4 w-4 text-green-500" />
                        ) : check.verdict === "Disputed" ? (
                          <AlertTriangle className="mt-0.5 h-4 w-4 text-yellow-500" />
                        ) : (
                          <Info className="mt-0.5 h-4 w-4 text-blue-500" />
                        )}
                        <div>
                          <p className="font-medium">Claim: {check.claim}</p>
                          <div className="mt-1 flex items-center space-x-2">
                            <span className="text-sm text-muted-foreground">Verdict:</span>
                            {getVerdictBadge(check.verdict)}
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">Source: {check.source}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-muted-foreground">No fact checks available</div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageSquare className="mr-2 h-5 w-5" />
            Conversation
          </CardTitle>
          <CardDescription>Your conversation about this article</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-4">
              <div className="flex justify-start">
                <div className="rounded-lg bg-muted px-4 py-2 max-w-[80%]">
                  How can I help you understand this article better?
                </div>
              </div>

              {/* This would be populated with actual chat messages */}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

