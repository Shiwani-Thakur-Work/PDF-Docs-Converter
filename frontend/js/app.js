document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
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

  // --- App State ---
  let currentMode = "convert"; // 'convert' | 'compress' | 'merge' | 'split'
  let targetFormat = "docx";   // 'docx' | 'pdf'
  let stagedFiles = [];
  let currentDownloadUrl = null;

  // --- Check Backend Health on Load ---
  fetch("/api/health")
    .then(r => r.json())
    .then(data => {
      if (data.status === "healthy") {
        const engineLabel = data.engines.docx2pdf_libreoffice === "available"
          ? "LibreOffice & pdf2docx Ready"
          : "pdf2docx & ReportLab Ready";
        engineStatusBadge.querySelector(".status-text").textContent = engineLabel;
      }
    })
    .catch(() => {
      engineStatusBadge.querySelector(".status-text").textContent = "Local Server";
    });

  // --- Mode Configurations ---
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

  // --- Switch Mode Handler ---
  function switchMode(newMode) {
    currentMode = newMode;
    const cfg = MODES[newMode];

    // Update tab active state
    tabButtons.forEach(btn => {
      const active = btn.dataset.mode === newMode;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active);
    });

    // Update labels and descriptions
    modeTitle.textContent = cfg.title;
    modeDesc.textContent = cfg.desc;
    btnProcessText.textContent = cfg.btnText;
    fileInput.accept = cfg.accept;
    fileInput.multiple = cfg.multiple;

    // Badges
    supportedFormatsBadge.innerHTML = cfg.badges
      .map(b => `<span class="badge">${b}</span>`)
      .join("");

    // Toggle specific controls
    targetBar.classList.toggle("hidden", currentMode !== "convert");
    splitControls.classList.toggle("hidden", currentMode !== "split");

    resetWorkspace();
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => switchMode(btn.dataset.mode));
  });

  // --- Target Format Switcher ---
  btnTargetDocx.addEventListener("click", () => setTargetFormat("docx"));
  btnTargetPdf.addEventListener("click", () => setTargetFormat("pdf"));

  function setTargetFormat(fmt) {
    targetFormat = fmt;
    btnTargetDocx.classList.toggle("active", fmt === "docx");
    btnTargetPdf.classList.toggle("active", fmt === "pdf");
  }

  // --- File Selection & Staging ---
  fileInput.addEventListener("change", (e) => {
    handleFiles(e.target.files);
  });

  // Drag and Drop Effects
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

    // Format file details
    if (currentMode === "merge") {
      stagedFileName.textContent = `${stagedFiles.length} PDF files selected`;
      const totalBytes = stagedFiles.reduce((acc, f) => acc + f.size, 0);
      stagedFileSize.textContent = formatBytes(totalBytes);
      fileTypeIcon.textContent = "📚";
    } else {
      const file = stagedFiles[0];
      stagedFileName.textContent = file.name;
      stagedFileSize.textContent = formatBytes(file.size);

      // Auto-detect target format in convert mode
      const ext = file.name.split(".").pop().toLowerCase();
      if (ext === "pdf") {
        fileTypeIcon.textContent = "📕";
        setTargetFormat("docx");
      } else if (ext === "docx" || ext === "doc") {
        fileTypeIcon.textContent = "📘";
        setTargetFormat("pdf");
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

    if (currentDownloadUrl) {
      URL.revokeObjectURL(currentDownloadUrl);
      currentDownloadUrl = null;
    }
  }

  // --- Process & Conversion Execution ---
  btnProcess.addEventListener("click", async () => {
    if (stagedFiles.length === 0) return;

    hideError();
    resultCard.classList.add("hidden");
    btnProcess.disabled = true;
    progressSection.classList.remove("hidden");
    setProgress(15, "Uploading document...");

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

    // Execute Request via XMLHttpRequest for real upload tracking
    const xhr = new XMLHttpRequest();
    xhr.open("POST", endpoint, true);
    xhr.responseType = "blob";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 60);
        setProgress(Math.max(15, percent), "Uploading file...");
      }
    };

    xhr.onload = async () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(100, "Finalizing download...");
        
        // Parse filename from Content-Disposition header if available
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
        currentDownloadUrl = URL.createObjectURL(blob);
        btnDownload.href = currentDownloadUrl;
        btnDownload.download = downloadName;

        setTimeout(() => {
          progressSection.classList.add("hidden");
          resultDetails.textContent = `Generated: ${downloadName} (${formatBytes(blob.size)})`;
          resultCard.classList.remove("hidden");
          btnProcess.disabled = false;
        }, 350);
      } else {
        // Handle error response from blob
        progressSection.classList.add("hidden");
        btnProcess.disabled = false;
        try {
          const errText = await xhr.response.text();
          const errJson = JSON.parse(errText);
          showError(errJson.message || "Conversion failed. Please verify your document.");
        } catch {
          showError("Conversion failed. Please verify the document format and try again.");
        }
      }
    };

    xhr.onerror = () => {
      progressSection.classList.add("hidden");
      btnProcess.disabled = false;
      showError("Network error or connection lost. Please ensure the server is running.");
    };

    // Incremental progress simulation during backend processing
    let processingSim = 65;
    const simInterval = setInterval(() => {
      if (xhr.readyState === 4) {
        clearInterval(simInterval);
      } else if (processingSim < 95) {
        processingSim += 5;
        setProgress(processingSim, "Converting & reconstructing layout...");
      }
    }, 600);

    xhr.send(formData);
  });

  // --- UI Helpers ---
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
