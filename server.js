const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const { exec } = require("child_process");

const app = express();

app.use(express.static("public"));
app.use("/uploads", express.static("uploads"));
app.use("/output", express.static("output"));
// Needed to parse json bodies
app.use(express.json());

// Ensure folders exist (هنا بيكريت فولدر القطع المؤقتة لوحده)
["uploads", "output", "temp_chunks"].forEach(dir => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
});

// Configure multer for temp chunk storage
const uploadChunk = multer({ dest: "temp_chunks/" });

// 1) Chunk Upload Endpoint (ده المسار اللي كان ناقص وبيجيب 404)
app.post("/upload/chunk", uploadChunk.single("chunk"), (req, res) => {
  try {
    const { sessionId, fileType, chunkIndex } = req.body;
    
    if (!req.file) {
      return res.status(400).json({ success: false, error: "No chunk file received" });
    }
    
    // Rename the chunk to a structured format for easy assembly
    const chunkPath = path.join("temp_chunks", `${sessionId}_${fileType}_${chunkIndex}`);
    fs.renameSync(req.file.path, chunkPath);
    
    res.json({ success: true, message: `Chunk ${chunkIndex} received` });
  } catch (error) {
    console.error("Chunk Error:", error);
    res.status(500).json({ success: false, error: "Chunk processing failed." });
  }
});

// Assembly helper (دالة تجميع القطع بعد ما الرفع يخلص)
const assembleFile = async (sessionId, fileType, originalName, totalChunks) => {
   const ext = path.extname(originalName);
   const finalName = `${sessionId}_${fileType}${ext}`;
   const finalPath = path.join("uploads", finalName);
   const writeStream = fs.createWriteStream(finalPath);
   
   for(let i=0; i<totalChunks; i++) {
      const chunkPath = path.join("temp_chunks", `${sessionId}_${fileType}_${i}`);
      await new Promise((resolve, reject) => {
         if (!fs.existsSync(chunkPath)) {
            return reject(new Error(`Missing chunk ${i} for ${fileType}`));
         }
         const readStream = fs.createReadStream(chunkPath);
         readStream.pipe(writeStream, { end: false });
         readStream.on("end", () => {
            fs.unlinkSync(chunkPath); // delete temp chunk
            resolve();
         });
         readStream.on("error", reject);
      });
   }
   
   await new Promise(resolve => {
     writeStream.on('finish', resolve);
     writeStream.end();
   });
   
   return finalPath;
};


// 2) Complete & Process Endpoint (لما الرفع يخلص بالكامل ونشغل بايثون)
app.post("/upload/complete", async (req, res) => {
  try {
    const { sessionId, files, originalNames } = req.body; 

    let hdrPath = "";
    let datPath = "";
    let csvPath = ""; // تم إضافة مسار ملف الـ CSV

    // Assemble all files (hdr, dat, and optionally csv)
    for (const file of files) {
       const pathStr = await assembleFile(sessionId, file.type, originalNames[file.type], file.chunks);
       if (file.type === "hdr") hdrPath = `./${pathStr}`;
       if (file.type === "dat") datPath = `./${pathStr}`;
       if (file.type === "csv") csvPath = `./${pathStr}`; // تجميع الـ CSV لو موجود
    }

    console.log("Files assembled. Running Python pipeline...");
    
    // Just a trick to get the dat file's base name to match output behavior in python script
    const outputDatName = path.basename(datPath); 

    // بناء أمر التشغيل بناءً على وجود ملف الـ CSV أو عدمه (مع إضافة علامات تنصيص للمسارات)
    const cmd = csvPath 
        ? `python ./ai_model/predict.py "${hdrPath}" "${datPath}" "${csvPath}"` 
        : `python ./ai_model/predict.py "${hdrPath}" "${datPath}"`;
        
    console.log("Executing:", cmd);

    exec(cmd, (err, stdout, stderr) => {
      if (err) {
        console.error("Python Error:", err);
        return res.status(500).json({ success: false, error: stderr || err.message });
      }

      console.log("Python Output:", stdout);

      let parsedReport = null;
      const jsonMatch = stdout.match(/###JSON_START###([\s\S]*?)###JSON_END###/);
      if (jsonMatch && jsonMatch[1]) {
        try {
          parsedReport = JSON.parse(jsonMatch[1]);
        } catch (e) {
          console.error("Failed to parse Python JSON report", e);
        }
      }

      res.json({
        success: true,
        imageUrl: `/output/${outputDatName}.png`,
        report: parsedReport
      });
    });

  } catch (err) {
    console.error("Assembly/Execution Error:", err);
    res.status(500).json({ success: false, error: err.message });
  }
});

const server = app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});

server.requestTimeout = 0;
server.headersTimeout = 0;
server.keepAliveTimeout = 0;
server.setTimeout(0);