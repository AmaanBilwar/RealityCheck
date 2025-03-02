'use client'
import { Suspense } from "react"
import NewsAnalyzer from "@/components/news-analyzer"
import { Skeleton } from "@/components/ui/skeleton"
import { SidebarProvider } from "@/components/ui/sidebar"
import AppSidebar from "@/components/app-sidebar"
import ChatInput from "@/components/chat-input"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"
import ErrorBoundary from "@/components/error-boundary"
import { cn } from "@/lib/utils"

export default function Home() {
    return (
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <SidebarProvider defaultOpen={true}>
          <div className="flex h-screen w-screen bg-gradient-to-br from-background to-muted/20 overflow-hidden">
            {/* Full-height Sidebar */}
            <div className="h-full">
              <AppSidebar />
            </div>
  
            {/* Main Content Area */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Fixed Header */}
              <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 shrink-0">
                <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                      RealityCheck
                    </span>
                    <span className="hidden md:block text-sm text-muted-foreground/80">
                      Intelligent News Verification
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="hidden sm:block">
                      <span className="text-sm text-muted-foreground/90 font-medium px-3 py-1 bg-muted/50 rounded-full">
                        Powered by xAI
                      </span>
                    </div>
                    <ModeToggle />
                  </div>
                </div>
              </header>
  
              {/* Main Content Layout - Modified for better spacing */}
              <main className="flex-1 overflow-y-auto px-4 py-8 md:px-6 md:py-8">
                <div className="mx-auto max-w-4xl flex flex-col gap-10 pb-24">
                  {/* Hero Section */}
                  <div className="text-center space-y-4 shrink-0">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                      Verify News with Precision
                    </h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                      Analyze articles, detect bias, and verify facts with our advanced AI system. Paste a URL or text to get started.
                    </p>
                  </div>
  
                  {/* News Analyzer - Takes most of the space */}
                  <div className="bg-card rounded-xl shadow-lg border border-border/50 p-6 hover:shadow-xl transition-all duration-300">
                    <ErrorBoundary 
                      fallback={
                        <div className="text-center text-destructive py-8 flex flex-col justify-center">
                          <p className="font-medium">Oops! Something went wrong.</p>
                          <p className="text-sm mt-2">Please refresh or try again later.</p>
                        </div>
                      }
                    >
                      <Suspense 
                        fallback={
                          <div className="space-y-4">
                            <Skeleton className="h-12 w-full rounded-lg" />
                            <Skeleton className="h-[400px] w-full rounded-lg" />
                          </div>
                        }
                      >
                        <NewsAnalyzer />
                      </Suspense>
                    </ErrorBoundary>
                  </div>
                </div>
              </main>
  
              {/* Fixed Chat Section at Bottom - Separated from main scroll area */}
              <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 shrink-0">
                <div className="container mx-auto max-w-4xl px-4 py-4 md:px-6">
                  <div className="bg-card rounded-lg shadow-md border border-border/50 p-4">
                    <h3 className="text-lg font-semibold mb-3">Ask Follow-ups</h3>
                    <ChatInput />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </SidebarProvider>
      </ThemeProvider>
  )
}