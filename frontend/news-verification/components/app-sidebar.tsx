"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarTrigger,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar"
import axios from "axios"

import { MessageSquare, Plus, Clock, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

// Define the Thread interface for better type safety
interface Thread {
  id: string;
  topic: string;
}

export default function AppSidebar() {
  const router = useRouter()
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Note: Use GET not POST for fetching topics
        const response = await axios.get('http://127.0.0.1:8000/api/topics');
        if (response.data.topics) {
          setThreads(response.data.topics);
          console.log("Fetched topics:", response.data.topics);
        }
      } catch (err) {
        console.error("Failed to fetch topics:", err);
        setError("Failed to load topics. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTopics();
  }, []);

  // Handle creating a new thread
  const handleNewThread = () => {
    router.push('/new-thread');
  };

  // Handle clicking on an existing thread
  const handleThreadClick = (threadId: string) => {
    setActiveThreadId(threadId);
    router.push(`/thread/${threadId}`);
  };

  return (
    <Sidebar>
      <SidebarHeader className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <MessageSquare className="mr-2 h-5 w-5" />
          <span className="font-medium">News Topics</span>
        </div>
        <SidebarTrigger />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <div className="px-4 py-2">
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={handleNewThread}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Topic
            </Button>
          </div>
          <SidebarGroupContent>
            <ScrollArea className="h-[calc(100vh-120px)]">
              {isLoading ? (
                <div className="flex justify-center p-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : error ? (
                <div className="text-center p-4 text-red-500 flex flex-col items-center">
                  <AlertCircle className="h-5 w-5 mb-2" />
                  <p className="text-sm">{error}</p>
                </div>
              ) : (
                <SidebarMenu>
                  {threads.length === 0 ? (
                    <div className="px-4 py-3 text-sm text-muted-foreground">
                      No topics found. Create a new one to get started.
                    </div>
                  ) : (
                    threads.map((thread) => (
                      <SidebarMenuItem key={thread.id}>
                        <SidebarMenuButton 
                          isActive={activeThreadId === thread.id}
                          onClick={() => handleThreadClick(thread.id)}
                          className="flex flex-col items-start w-full text-left hover:bg-muted/50 transition-colors"
                        >
                          <span className="text-sm font-medium break-words whitespace-normal line-clamp-2 w-full">
                            {thread.topic}
                          </span>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))
                  )}
                </SidebarMenu>
              )}
            </ScrollArea>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}