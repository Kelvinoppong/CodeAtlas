"use client";

import { useState, useEffect } from "react";
import { FileTree } from "@/components/FileTree";
import { CenterCanvas } from "@/components/CenterCanvas";
import { CodeEditor } from "@/components/CodeEditor";
import { Header } from "@/components/Header";
import { ProjectImport } from "@/components/ProjectImport";
import { useAppStore } from "@/lib/store";
import api from "@/lib/api";

export default function Home() {
  const [showImport, setShowImport] = useState(false);
  const {
    currentProject,
    currentSnapshot,
    selectedFile,
    activeTab,
    setSelectedFile,
    setActiveTab,
    setCurrentProject,
    setCurrentSnapshot,
    setFileTree,
    setFileContent,
    setIsLoadingFile,
  } = useAppStore();

  // Load file content when selected
  useEffect(() => {
    if (selectedFile && currentSnapshot) {
      setIsLoadingFile(true);
      api
        .getFileContent(currentSnapshot.id, selectedFile)
        .then((content) => {
          setFileContent(content);
        })
        .catch((err) => {
          console.error("Failed to load file:", err);
          setFileContent(null);
        })
        .finally(() => {
          setIsLoadingFile(false);
        });
    }
  }, [selectedFile, currentSnapshot, setFileContent, setIsLoadingFile]);

  // Check for existing projects on mount
  useEffect(() => {
    api
      .listProjects()
      .then(async (projects) => {
        if (projects.length > 0) {
          const project = projects[0];
          setCurrentProject(project);

          // Get latest snapshot
          if (project.snapshot_count > 0) {
            try {
              const snapshots = await api.listProjectSnapshots(project.id);
              if (snapshots.length > 0) {
                const latestSnapshot = snapshots[0];
                const snapshotDetails = await api.getSnapshotStatus(latestSnapshot.snapshot_id);
                setCurrentSnapshot(snapshotDetails);
                
                // Load file tree
                const tree = await api.getFileTree(latestSnapshot.snapshot_id);
                setFileTree(tree);
              }
            } catch (err) {
              console.error("Failed to load snapshots:", err);
            }
          }
        }
      })
      .catch((err) => {
        console.log("Could not connect to API:", err.message);
      });
  }, [setCurrentProject, setCurrentSnapshot, setFileTree]);

  const handleImportSuccess = () => {
    setShowImport(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-arb-bg overflow-hidden">
      {/* Top Header */}
      <Header onImportClick={() => setShowImport(true)} />

      {/* Main 3-Pane Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - File Tree */}
        <aside className="w-72 flex-shrink-0 border-r border-arb-border bg-arb-panel flex flex-col animate-fade-in">
          <FileTree
            onFileSelect={setSelectedFile}
            selectedFile={selectedFile}
            onImportClick={() => setShowImport(true)}
          />
        </aside>

        {/* Center Panel - Graph/Chat Canvas */}
        <main className="flex-1 flex flex-col overflow-hidden bg-arb-bg animate-fade-in">
          <CenterCanvas activeTab={activeTab} onTabChange={setActiveTab} />
        </main>

        {/* Right Panel - Code Editor */}
        <aside className="w-[480px] flex-shrink-0 border-l border-arb-border bg-arb-panel flex flex-col animate-fade-in">
          <CodeEditor selectedFile={selectedFile} />
        </aside>
      </div>

      {/* Import Modal */}
      {showImport && (
        <ProjectImport
          onClose={() => setShowImport(false)}
          onSuccess={handleImportSuccess}
        />
      )}
    </div>
  );
}
