"use client"

import { useState } from "react"
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
import { MessageSquare, Plus, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

export default function AppSidebar() {
  const [threads, setThreads] = useState([
    { id: 1, title: "Climate Change Report Analysis", date: "2 hours ago", active: true },
    { id: 2, title: "Tech Industry Layoffs", date: "Yesterday", active: false },
    { id: 3, title: "Renewable Energy Study", date: "3 days ago", active: false },
    { id: 4, title: "Political Speech Fact-Check", date: "1 week ago", active: false },
    { id: 5, title: "Economic Forecast Review", date: "2 weeks ago", active: false },
  ])

  return (
    <Sidebar>
      <SidebarHeader className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <MessageSquare className="mr-2 h-5 w-5" />
          <span className="font-medium">Threads</span>
        </div>
        <SidebarTrigger />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <div className="px-4 py-2">
            <Button className="w-full justify-start" variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              New Thread
            </Button>
          </div>
          <SidebarGroupContent>
            <ScrollArea className="h-[calc(100vh-120px)]">
              <SidebarMenu>
                {threads.map((thread) => (
                  <SidebarMenuItem key={thread.id}>
                    <SidebarMenuButton isActive={thread.active} className="flex flex-col items-start">
                      <span className="text-sm font-medium">{thread.title}</span>
                      <div className="mt-1 flex items-center text-xs text-muted-foreground">
                        <Clock className="mr-1 h-3 w-3" />
                        {thread.date}
                      </div>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </ScrollArea>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

