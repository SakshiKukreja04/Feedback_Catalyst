const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const XLSX = require('xlsx');
const PDFDocument = require('pdfkit');
const { ChartJSNodeCanvas } = require('chartjs-node-canvas');

const app = express();
const port = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// Configure multer for file upload
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const fileFilter = (req, file, cb) => {
  // Accept only csv and xlsx files
  if (file.mimetype === 'text/csv' || 
      file.mimetype === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type. Only CSV and Excel files are allowed.'), false);
  }
};

const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB limit
  }
});

// Function to parse file and extract data
const parseFile = (filePath) => {
  const fileExtension = path.extname(filePath).toLowerCase();
  
  if (fileExtension === '.csv') {
    const workbook = XLSX.readFile(filePath, { type: 'file' });
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    return XLSX.utils.sheet_to_json(worksheet, { header: 1 });
  } else if (fileExtension === '.xlsx') {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    return XLSX.utils.sheet_to_json(worksheet, { header: 1 });
  }
  
  throw new Error('Unsupported file format');
};

// Function to generate charts
const generateChart = async (data, labels, title, type = 'bar') => {
  const width = 600;
  const height = 400;
  const chartCallback = (ChartJS) => {
    ChartJS.defaults.responsive = true;
    ChartJS.defaults.maintainAspectRatio = false;
  };
  
  const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height, chartCallback });
  
  const configuration = {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: title,
        data: data,
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: title,
          font: {
            size: 16
          }
        },
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  };
  
  return await chartJSNodeCanvas.renderToBuffer(configuration);
};

// Function to generate PDF report
const generatePDFReport = async (data, reportConfig) => {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({ margin: 50 });
      const chunks = [];
      
      doc.on('data', chunk => chunks.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(chunks)));
      
      // Add title
      doc.fontSize(24)
         .font('Helvetica-Bold')
         .text('Feedback Analysis Report', { align: 'center' });
      
      doc.moveDown();
      doc.fontSize(12)
         .font('Helvetica')
         .text(`Generated on: ${new Date().toLocaleDateString()}`, { align: 'center' });
      
      doc.moveDown(2);
      
      // Add report type
      doc.fontSize(16)
         .font('Helvetica-Bold')
         .text(`Report Type: ${reportConfig.reportType === 'generalized' ? 'Generalized Report' : 'Field-Wise Report'}`);
      
      doc.moveDown();
      
      if (reportConfig.reportType === 'generalized') {
        // Handle generalized report
        doc.fontSize(14)
           .font('Helvetica-Bold')
           .text('Comparisons:');
        
        reportConfig.comparisons.forEach((comparison, index) => {
          doc.moveDown(0.5);
          doc.fontSize(12)
             .font('Helvetica')
             .text(`${index + 1}. ${comparison.field1} vs ${comparison.field2}`);
          
          // Add data summary for this comparison
          const field1Data = data.map(row => row[data[0].indexOf(comparison.field1)]);
          const field2Data = data.map(row => row[data[0].indexOf(comparison.field2)]);
          
          // Count unique values
          const field1Counts = {};
          const field2Counts = {};
          
          field1Data.slice(1).forEach(value => {
            field1Counts[value] = (field1Counts[value] || 0) + 1;
          });
          
          field2Data.slice(1).forEach(value => {
            field2Counts[value] = (field2Counts[value] || 0) + 1;
          });
          
          doc.moveDown(0.5);
          doc.fontSize(10)
             .font('Helvetica')
             .text(`${comparison.field1} unique values: ${Object.keys(field1Counts).length}`);
          doc.text(`${comparison.field2} unique values: ${Object.keys(field2Counts).length}`);
        });
      } else {
        // Handle field-wise report
        doc.fontSize(14)
           .font('Helvetica-Bold')
           .text('Field Selection:');
        
        doc.moveDown(0.5);
        doc.fontSize(12)
           .font('Helvetica')
           .text(`Year Field: ${reportConfig.selection.year}`);
        doc.text(`Facility Field: ${reportConfig.selection.facility}`);
        
        // Add data summary
        const yearData = data.map(row => row[data[0].indexOf(reportConfig.selection.year)]);
        const facilityData = data.map(row => row[data[0].indexOf(reportConfig.selection.facility)]);
        
        const yearCounts = {};
        const facilityCounts = {};
        
        yearData.slice(1).forEach(value => {
          yearCounts[value] = (yearCounts[value] || 0) + 1;
        });
        
        facilityData.slice(1).forEach(value => {
          facilityCounts[value] = (facilityCounts[value] || 0) + 1;
        });
        
        doc.moveDown();
        doc.fontSize(12)
           .font('Helvetica-Bold')
           .text('Data Summary:');
        
        doc.fontSize(10)
           .font('Helvetica')
           .text(`Total records: ${data.length - 1}`);
        doc.text(`Unique years: ${Object.keys(yearCounts).length}`);
        doc.text(`Unique facilities: ${Object.keys(facilityCounts).length}`);
      }
      
      // Add data table
      doc.moveDown(2);
      doc.fontSize(14)
         .font('Helvetica-Bold')
         .text('Sample Data (First 10 rows):');
      
      doc.moveDown();
      
      // Create table headers
      const headers = data[0];
      const tableTop = doc.y;
      let tableLeft = 50;
      const colWidth = (doc.page.width - 100) / headers.length;
      
      headers.forEach((header, i) => {
        doc.fontSize(10)
           .font('Helvetica-Bold')
           .text(header, tableLeft + (i * colWidth), tableTop, { width: colWidth });
      });
      
      // Add table data
      const sampleData = data.slice(1, 11);
      sampleData.forEach((row, rowIndex) => {
        const rowY = tableTop + 20 + (rowIndex * 15);
        row.forEach((cell, colIndex) => {
          doc.fontSize(8)
             .font('Helvetica')
             .text(String(cell || ''), tableLeft + (colIndex * colWidth), rowY, { width: colWidth });
        });
      });
      
      doc.end();
    } catch (error) {
      reject(error);
    }
  });
};

// Routes
app.post('/upload', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    res.json({
      message: 'File uploaded successfully',
      filename: req.file.filename
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Error uploading file' });
  }
});

// Extract headers from uploaded file
app.get('/headers/:filename', (req, res) => {
  try {
    const filePath = path.join(__dirname, 'uploads', req.params.filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const data = parseFile(filePath);
    const headers = data[0];
    
    res.json({ headers });
  } catch (error) {
    console.error('Header extraction error:', error);
    res.status(500).json({ error: 'Error extracting headers' });
  }
});

// Generate PDF report
app.post('/generate-report', async (req, res) => {
  try {
    const { reportType, filename, comparisons, selection } = req.body;
    
    if (!filename) {
      return res.status(400).json({ error: 'No filename provided' });
    }
    
    const filePath = path.join(__dirname, 'uploads', filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const data = parseFile(filePath);
    
    const reportConfig = {
      reportType,
      comparisons,
      selection
    };
    
    const pdfBuffer = await generatePDFReport(data, reportConfig);
    
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename=feedback-report.pdf');
    res.send(pdfBuffer);
    
  } catch (error) {
    console.error('PDF generation error:', error);
    res.status(500).json({ error: 'Error generating PDF report' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File size too large. Maximum size is 5MB.' });
    }
    return res.status(400).json({ error: err.message });
  }
  res.status(500).json({ error: err.message });
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
}); 