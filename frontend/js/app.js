/**
 * DocFlow Frontend Controller
 * ===========================
 * Handles user interactions, drag-and-drop file ingestion, dynamic mode switching,
 * real-time upload progress interpolation, and bi-directional API/Client-side execution.
 *
 * Designed to work seamlessly both with the local Python backend and as a standalone
 * client-side utility on static hosts like GitHub Pages.
 */

document.addEventListener("DOMContentLoaded", () => {
  // =========================================================================
  // DOM Elements Selection
  // =========================================================================
  const tabButtons = document.querySelectorAll(".tab-btn");
  const modeTitle = document.getElementById("modeTitle");
  const modeDesc = document.getElementById("modeDesc");
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropzonePrompt = document.getElementById("dropzonePrompt");
  const stagedFileCard = document.getElementById("stagedFileCard");
  const stagedFileName = document.getElementById("stagedFileName");
  const stagedFileSize = document.getElementById("stagedFileSize");
  const fileTypeIcon = document.getElementById("fileTypeIcon");
  const btnClearFile = document.getElementById("btnClearFile");
  const supportedFormatsBadge = document.getElementById("supportedFormatsBadge");
  const targetBar = document.getElementById("targetBar");
  const btnTargetDocx = document.getElementById("btnTargetDocx");
  const btnTargetPdf = document.getElementById("btnTargetPdf");
  const splitControls = document.getElementById("splitControls");
  const splitPagesInput = document.getElementById("splitPagesInput");
  const btnProcess = document.getElementById("btnProcess");
  const btnProcessText = document.getElementById("btnProcessText");
  const progressSection = document.getElementById("progressSection");
  const progressStatus = document.getElementById("progressStatus");
  const progressPercent = document.getElementById("progressPercent");
  const progressBarFill = document.getElementById("progressBarFill");
  const resultCard = document.getElementById("resultCard");
  const resultDetails = document.getElementById("resultDetails");
  const btnDownload = document.getElementById("btnDownload");
  const btnReset = document.getElementById("btnReset");
  const errorBanner = document.getElementById("errorBanner");
  const errorMessage = document.getElementById("errorMessage");
  const engineStatusBadge = document.getElementById("engineStatusBadge");

  // =========================================================================
  // Application State
  // =========================================================================
  let currentMode = "convert";     // Active tool mode: 'convert' | 'compress' | 'merge' | 'split'
  let targetFormat = "docx";       // Target format for convert mode: 'docx' | 'pdf'
  let stagedFiles = [];            // Array of selected File objects
  let currentDownloadUrl = null;   // Active Blob object URL for memory cleanup
  let backendAvailable = false;    // Whether local Python FastAPI server is active

  // =========================================================================
  // Server Health Probe & Engine Auto-Detection
  // =========================================================================
  fetch("/api/health")
    .then(r => r.json())
    .then(data => {
      if (data.status === "healthy") {
        backendAvailable = true;
        const engineLabel = data.engines.docx2pdf_libreoffice === "available"
          ? "LibreOffice & pdf2docx Ready"
          : "pdf2docx & ReportLab Ready";
        engineStatusBadge.querySelector(".status-text").textContent = engineLabel;
      }
    })
    .catch(() => {
      // Running statically (e.g., GitHub Pages)
      backendAvailable = false;
      engineStatusBadge.querySelector(".status-text").textContent = "Browser Engine Ready";
    });

  // =========================================================================
  // Tool Modes Configuration Map
  // =========================================================================
  const MODES = {
    convert: {
      title: "PDF ⇄ DOCX Converter",
      desc: "Convert PDF to editable Word or DOCX to PDF with 100% layout and table fidelity.",
      accept: ".pdf,.docx,.doc",
      btnText: "Convert File",
      multiple: false,
      badges: ["PDF", "DOCX", "DOC"]
    },
    compress: {
      title: "Compress PDF Document",
      desc: "Reduce PDF file size via stream optimization and object deduplication without sacrificing readability.",
      accept: ".pdf",
      btnText: "Compress PDF",
      multiple: false,
      badges: ["PDF"]
    },
    merge: {
      title: "Merge Multiple PDFs",
      desc: "Combine two or more PDF documents into a single unified file in seconds.",
      accept: ".pdf",
      btnText: "Merge PDFs",
      multiple: true,
      badges: ["Select 2+ PDFs"]
    },
    split: {
      title: "Split PDF Pages",
      desc: "Extract specific pages or page ranges into a new standalone PDF.",
      accept: ".pdf",
      btnText: "Extract Pages",
      multiple: false,
      badges: ["PDF"]
    }
  };

  // =========================================================================
  // Mode Navigation Handler
  // =========================================================================
  function switchMode(newMode) {
    currentMode = newMode;
    const cfg = MODES[newMode];

    // Update active tab buttons
    tabButtons.forEach(btn => {
      const active = btn.dataset.mode === newMode;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active);
    });

    // Update headings and input constraints
    modeTitle.textContent = cfg.title;
    modeDesc.textContent = cfg.desc;
    btnProcessText.textContent = cfg.btnText;
    fileInput.accept = cfg.accept;
    fileInput.multiple = cfg.multiple;

    // Refresh format badges
    supportedFormatsBadge.innerHTML = cfg.badges
      .map(b => `<span class="badge">${b}</span>`)
      .join("");

    // Toggle mode-specific control panels
    targetBar.classList.toggle("hidden", currentMode !== "convert");
    splitControls.classList.toggle("hidden", currentMode !== "split");

    resetWorkspace();
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => switchMode(btn.dataset.mode));
  });

  // =========================================================================
  // Target Format Switching (Convert Mode)
  // =========================================================================
  btnTargetDocx.addEventListener("click", () => setTargetFormat("docx"));
  btnTargetPdf.addEventListener("click", () => setTargetFormat("pdf"));

  function setTargetFormat(fmt) {
    targetFormat = fmt;
    btnTargetDocx.classList.toggle("active", fmt === "docx");
    btnTargetPdf.classList.toggle("active", fmt === "pdf");
  }

  // =========================================================================
  // File Staging & Drag-and-Drop Handlers
  // =========================================================================
  fileInput.addEventListener("change", (e) => {
    handleFiles(e.target.files);
  });

  // Visual dragover highlights
  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  });

  function handleFiles(fileList) {
    hideError();
    if (!fileList || fileList.length === 0) return;

    stagedFiles = Array.from(fileList);

    if (currentMode === "merge") {
      // Multi-file summary display
      stagedFileName.textContent = `${stagedFiles.length} PDF files selected`;
      const totalBytes = stagedFiles.reduce((acc, f) => acc + f.size, 0);
      stagedFileSize.textContent = formatBytes(totalBytes);
      fileTypeIcon.textContent = "📚";
    } else {
      // Single file display with format auto-detection
      const file = stagedFiles[0];
      stagedFileName.textContent = file.name;
      stagedFileSize.textContent = formatBytes(file.size);

      const ext = file.name.split(".").pop().toLowerCase();
      if (ext === "pdf") {
        fileTypeIcon.textContent = "📕";
        setTargetFormat("docx"); // Auto-suggest Word output when uploading PDF
      } else if (ext === "docx" || ext === "doc") {
        fileTypeIcon.textContent = "📘";
        setTargetFormat("pdf");  // Auto-suggest PDF output when uploading Word
      } else {
        fileTypeIcon.textContent = "📄";
      }
    }

    dropzonePrompt.classList.add("hidden");
    stagedFileCard.classList.remove("hidden");
    btnProcess.disabled = false;
  }

  btnClearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    resetWorkspace();
  });

  btnReset.addEventListener("click", () => {
    resetWorkspace();
  });

  function resetWorkspace() {
    stagedFiles = [];
    fileInput.value = "";
    splitPagesInput.value = "";
    dropzonePrompt.classList.remove("hidden");
    stagedFileCard.classList.add("hidden");
    btnProcess.disabled = true;
    progressSection.classList.add("hidden");
    resultCard.classList.add("hidden");
    hideError();

    // Revoke previous Blob URL to prevent memory leaks in the browser
    if (currentDownloadUrl) {
      URL.revokeObjectURL(currentDownloadUrl);
      currentDownloadUrl = null;
    }
  }

  // =========================================================================
  // Client-Side Fallback Utilities (Runs in browser if backend is offline)
  // =========================================================================
  async function runClientSideMerge(files) {
    setProgress(30, "Merging PDF pages in browser...");
    const mergedPdf = await PDFLib.PDFDocument.create();
    for (const f of files) {
      const arrayBuffer = await f.arrayBuffer();
      const pdf = await PDFLib.PDFDocument.load(arrayBuffer);
      const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
      copiedPages.forEach((page) => mergedPdf.addPage(page));
    }
    setProgress(90, "Assembling document...");
    const mergedBytes = await mergedPdf.save();
    return new Blob([mergedBytes], { type: "application/pdf" });
  }

  async function runClientSideSplit(file, pageRangeStr) {
    setProgress(30, "Reading PDF in browser...");
    const arrayBuffer = await file.arrayBuffer();
    const srcPdf = await PDFLib.PDFDocument.load(arrayBuffer);
    const totalPages = srcPdf.getPageCount();

    const selectedIndices = [];
    const parts = pageRangeStr.split(",").map(p => p.trim()).filter(Boolean);
    for (const part of parts) {
      if (part.includes("-")) {
        const [s, e] = part.split("-").map(n => parseInt(n.trim(), 10));
        const start = Math.max(1, s);
        const end = Math.min(totalPages, e);
        for (let i = start; i <= end; i++) selectedIndices.push(i - 1);
      } else {
        const num = parseInt(part, 10);
        if (num >= 1 && num <= totalPages) selectedIndices.push(num - 1);
      }
    }

    if (selectedIndices.length === 0) {
      throw new Error(`No valid pages found in range. Document has ${totalPages} pages.`);
    }

    const uniqueIndices = [...new Set(selectedIndices)];
    const outPdf = await PDFLib.PDFDocument.create();
    const copiedPages = await outPdf.copyPages(srcPdf, uniqueIndices);
    copiedPages.forEach(p => outPdf.addPage(p));

    setProgress(90, "Extracting pages...");
    const outBytes = await outPdf.save();
    return new Blob([outBytes], { type: "application/pdf" });
  }

  // =========================================================================
  // Process Execution Workflow
  // =========================================================================
  btnProcess.addEventListener("click", async () => {
    if (stagedFiles.length === 0) return;

    hideError();
    resultCard.classList.add("hidden");
    btnProcess.disabled = true;
    progressSection.classList.remove("hidden");
    setProgress(15, "Initializing conversion task...");

    // [Scenario A: Client-Side Execution on GitHub Pages without Backend]
    if (!backendAvailable && (currentMode === "merge" || currentMode === "split")) {
      try {
        let resultBlob;
        let outputName = "document.pdf";
        if (currentMode === "merge") {
          resultBlob = await runClientSideMerge(stagedFiles);
          outputName = "merged_document.pdf";
        } else {
          const pages = splitPagesInput.value.trim();
          if (!pages) throw new Error("Please specify page numbers to extract (e.g. 1-3, 5).");
          resultBlob = await runClientSideSplit(stagedFiles[0], pages);
          outputName = `${stagedFiles[0].name.replace(/\.pdf$/i, "")}_split.pdf`;
        }

        setProgress(100, "Done!");
        presentDownloadResult(resultBlob, outputName);
        return;
      } catch (err) {
        progressSection.classList.add("hidden");
        btnProcess.disabled = false;
        showError(err.message || "Operation failed.");
        return;
      }
    }

    if (!backendAvailable && currentMode === "convert") {
      progressSection.classList.add("hidden");
      btnProcess.disabled = false;
      showError("The DocFlow conversion engine runs locally via run.bat. Please start the local server to convert PDF to DOCX with high fidelity.");
      return;
    }

    // [Scenario B: Server-Backed Conversion Pipeline]
    const formData = new FormData();
    let endpoint = "";

    if (currentMode === "convert") {
      const file = stagedFiles[0];
      const ext = file.name.split(".").pop().toLowerCase();
      formData.append("file", file);

      if (targetFormat === "docx" || ext === "pdf") {
        endpoint = "/api/convert/pdf-to-docx";
      } else {
        endpoint = "/api/convert/docx-to-pdf";
      }
    } else if (currentMode === "compress") {
      formData.append("file", stagedFiles[0]);
      formData.append("level", "medium");
      endpoint = "/api/tools/compress-pdf";
    } else if (currentMode === "merge") {
      if (stagedFiles.length < 2) {
        showError("Please select at least 2 PDF files to merge.");
        progressSection.classList.add("hidden");
        btnProcess.disabled = false;
        return;
      }
      stagedFiles.forEach(f => formData.append("files", f));
      endpoint = "/api/tools/merge-pdf";
    } else if (currentMode === "split") {
      const pages = splitPagesInput.value.trim();
      if (!pages) {
        showError("Please specify page numbers or ranges to extract (e.g. 1-3, 5).");
        progressSection.classList.add("hidden");
        btnProcess.disabled = false;
        return;
      }
      formData.append("file", stagedFiles[0]);
      formData.append("pages", pages);
      endpoint = "/api/tools/split-pdf";
    }

    // Perform upload via XMLHttpRequest to measure network progress
    const xhr = new XMLHttpRequest();
    xhr.open("POST", endpoint, true);
    xhr.responseType = "blob";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 60);
        setProgress(Math.max(15, percent), "Uploading document...");
      }
    };

    xhr.onload = async () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(100, "Finalizing download artifact...");

        // Parse filename from Content-Disposition header (RFC 5987 UTF-8 or standard)
        let downloadName = "converted_document";
        const disposition = xhr.getResponseHeader("Content-Disposition");
        if (disposition) {
          const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
          if (utf8Match && utf8Match[1]) {
            downloadName = decodeURIComponent(utf8Match[1]);
          } else {
            const basicMatch = disposition.match(/filename="?([^";]+)"?/i);
            if (basicMatch && basicMatch[1]) downloadName = basicMatch[1];
          }
        }

        const blob = xhr.response;
        presentDownloadResult(blob, downloadName);
      } else {
        progressSection.classList.add("hidden");
        btnProcess.disabled = false;
        try {
          const errText = await xhr.response.text();
          const errJson = JSON.parse(errText);
          showError(errJson.message || "Conversion failed. Please verify your document.");
        } catch {
          showError("Conversion failed. Please verify document formatting and try again.");
        }
      }
    };

    xhr.onerror = () => {
      progressSection.classList.add("hidden");
      btnProcess.disabled = false;
      showError("Connection lost or server unreachable. Please verify the backend is running.");
    };

    // Incremental progress simulation during layout reconstruction
    let processingSim = 65;
    const simInterval = setInterval(() => {
      if (xhr.readyState === 4) {
        clearInterval(simInterval);
      } else if (processingSim < 95) {
        processingSim += 5;
        setProgress(processingSim, "Converting and reconstructing layout...");
      }
    }, 600);

    xhr.send(formData);
  });

  // =========================================================================
  // Download Result Presentation
  // =========================================================================
  function presentDownloadResult(blob, downloadName) {
    currentDownloadUrl = URL.createObjectURL(blob);
    btnDownload.href = currentDownloadUrl;
    btnDownload.download = downloadName;

    setTimeout(() => {
      progressSection.classList.add("hidden");
      resultDetails.textContent = `Generated: ${downloadName} (${formatBytes(blob.size)})`;
      resultCard.classList.remove("hidden");
      btnProcess.disabled = false;
    }, 350);
  }

  // =========================================================================
  // UI Helpers
  // =========================================================================
  function setProgress(percent, statusText) {
    progressBarFill.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;
    progressStatus.textContent = statusText;
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove("hidden");
  }

  function hideError() {
    errorBanner.classList.add("hidden");
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
});
