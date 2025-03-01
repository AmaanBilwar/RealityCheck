import { Suspense } from "react"
import NewsAnalyzer from "@/components/news-analyzer"
import { Skeleton } from "@/components/ui/skeleton"
import { SidebarProvider } from "@/components/ui/sidebar"
import AppSidebar from "@/components/app-sidebar"
import ChatInput from "@/components/chat-input"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"

export default function Home() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <SidebarProvider defaultOpen={true}>
        <div className="flex min-h-screen bg-background">
          <AppSidebar />
          <div className="flex-1">
            <header className="border-b">
              <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                <h1 className="text-xl font-semibold tracking-tight">NewsBot</h1>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-muted-foreground">Intelligent News Verification System</span>
                  <ModeToggle />
                </div>
              </div>
            </header>
            <main className="container mx-auto px-4 py-6 md:px-6 md:py-10">
              <div className="mx-auto max-w-4xl">
                <h2 className="mb-6 text-2xl font-bold tracking-tight">Analyze News Articles & Text</h2>
                <p className="mb-8 text-muted-foreground">
                  Enter a news article URL or paste text to analyze. Our system will highlight key points, determine
                  sentiment, and find related sources to help verify the information.
                </p>
                <Suspense fallback={<Skeleton className="h-[600px] w-full rounded-lg" />}>
                  <NewsAnalyzer />
                </Suspense>

                <div className="mt-8">
                  <ChatInput />
                </div>
              </div>
            </main>
          </div>
        </div>
      </SidebarProvider>
    </ThemeProvider>
  )
}

