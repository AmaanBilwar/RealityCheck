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

import { MessageSquare, Plus, Clock, AlertCircle, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"

// Define the Thread interface for better type safety
interface Thread {
  _id: string;
  topic: string;
}

export default function AppSidebar() {
  const router = useRouter()
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hoveredThreadId, setHoveredThreadId] = useState<string | null>(null)

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Note: Use GET not POST for fetching topics
        const response = await axios.get('http://localhost:8000/api/topics');
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
  const handleThreadClick = async (threadId: string) => {
    try {
      setActiveThreadId(threadId);
      
      // Show loading state while fetching thread data
      setIsLoading(true);
      
      // Fetch the thread data from API
      const response = await axios.get(`http://localhost:8000/api/thread/${threadId}`);
      
      if (response.data) {
        console.log("Fetched thread data:", response.data.Thread_Data);
        // Store thread data in local storage or state management if needed
        // This allows the thread page to access the data
        localStorage.setItem('currentThreadData', JSON.stringify(response.data.Thread_Data));
      }
      
      // Navigate to the thread page
      router.push(`/thread/${threadId}`);
    } catch (err) {
      console.error("Failed to fetch thread data:", err);
      // Still navigate to the thread page, which should handle the error case
      router.push(`/thread/${threadId}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Sidebar>
      <SidebarHeader className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <MessageSquare className="mr-2 h-5 w-5 text-primary" />
          <span className="font-medium">News Topics</span>
        </div>
        <SidebarTrigger />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <div className="px-4 py-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    className="w-full justify-start shadow-sm transition-all hover:shadow-md hover:translate-y-[-1px]" 
                    variant="default"
                    onClick={handleNewThread}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    New Topic
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Create a new news topic</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
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
                      <SidebarMenuItem key={thread._id}>
                        <SidebarMenuButton 
                          isActive={activeThreadId === thread._id}
                          onClick={() => handleThreadClick(thread._id)}
                          className={`flex flex-col items-start w-full text-left rounded-lg my-1 p-2.5 transition-all duration-200
                            ${activeThreadId === thread._id 
                              ? 'bg-primary/10 shadow-sm border-l-4 border-primary pl-2' 
                              : 'hover:bg-muted/70 hover:shadow-sm hover:translate-x-1'}`}
                          onMouseEnter={() => setHoveredThreadId(thread._id)}
                          onMouseLeave={() => setHoveredThreadId(null)}
                        >
                          <div className="flex justify-between items-center w-full">
                            <span className="text-sm font-medium break-words whitespace-normal line-clamp-2 w-full">
                              {thread.topic}
                            </span>
                            {hoveredThreadId === thread._id && activeThreadId !== thread._id && (
                              <Calendar className="h-3.5 w-3.5 text-muted-foreground opacity-70" />
                            )}
                          </div>
                          {activeThreadId === thread._id && (
                            <Badge className="mt-1.5 text-xs" variant="outline">Active</Badge>
                          )}
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