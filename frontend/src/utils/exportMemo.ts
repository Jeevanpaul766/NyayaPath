/**
 * NyayaPath — Citizen Legal Guidance Memo Exporter
 * Generates official structured legal opinion documents and print-ready PDFs.
 */

function generateDocId(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = 'NYP-';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export function downloadTextMemo(
  content: string, 
  regime?: string | null,
  offenceDate?: string | null,
  firDate?: string | null
) {
  const docId = generateDocId();
  const dateStr = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const regimeLabel = regime === 'bns_bnss'
    ? 'Bharatiya Nyaya Sanhita (BNS, 2023) & BNSS, 2023 [Post-July 1, 2024 Incident]'
    : regime === 'ipc_crpc'
    ? 'Indian Penal Code (IPC, 1860) & CrPC, 1973 [Pre-July 1, 2024 Incident]'
    : 'Ambiguous / Straddling Timeline [Dual-Regime Considerations]';

  const memoText = `# NYAYAPATH — CITIZEN LEGAL GUIDANCE MEMORANDUM
**Document ID:** ${docId}
**Date of Guidance:** ${dateStr}
**Governing Statutory Regime:** ${regimeLabel}
**Incident Date:** ${offenceDate || 'Not specified in query'}
**FIR Registration Date:** ${firDate || 'Not specified in query'}
**Verification Engine:** NyayaPath Hand-Verified Statutory Allowlist Gate

---

## MANDATORY STATUTORY NOTICE
*This memorandum contains educational legal information synthesized by the NyayaPath reasoning agent. It is designed to assist citizens in understanding criminal offences, procedural rights, and statutory transitions under Indian law. This document does not constitute formal legal representation under the Advocates Act, 1961. Always consult an advocate enrolled with the State Bar Council before initiating judicial proceedings.*

---

${content}

---

## FREE LEGAL AID & EMERGENCY HELPLINE DIRECTORY
- **National Legal Services Authority (NALSA):** Helpline 15100 (Toll-Free, 24x7)
- **Police Emergency:** 112
- **Women Helpline:** 181
- **Mental Health Helpline (Tele-MANAS):** 14416
- **District Legal Services Authority (DLSA):** Available at every District Court complex in India
- **Official Portal:** https://nalsa.gov.in
- **India Code (Official Gazette Repository):** https://indiacode.nic.in
`;

  const blob = new Blob([memoText], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `NyayaPath_Legal_Memo_${docId}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function printMemoAsPDF(
  content: string, 
  regime?: string | null,
  offenceDate?: string | null,
  firDate?: string | null
) {
  const docId = generateDocId();
  const dateStr = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const regimeLabel = regime === 'bns_bnss'
    ? 'Bharatiya Nyaya Sanhita (BNS, 2023) & BNSS, 2023 [Post-July 1, 2024 Incident]'
    : regime === 'ipc_crpc'
    ? 'Indian Penal Code (IPC, 1860) & CrPC, 1973 [Pre-July 1, 2024 Incident]'
    : 'Ambiguous / Straddling Timeline [Dual-Regime Considerations]';

  // Format basic markdown headers and bolding for the print document
  const formattedHtml = content
    .replace(/^### (.*$)/gim, '<h3 style="color: #1a365d; border-bottom: 2px solid #cbd5e1; padding-bottom: 4px; margin-top: 24px; font-size: 16px;">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 style="color: #0f172a; margin-top: 28px; font-size: 18px;">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #0f172a;">$1</strong>')
    .replace(/\n\n/g, '<p style="margin: 10px 0; line-height: 1.6; color: #334155; font-size: 13px;">')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n\d+\. /g, '<br>&nbsp;&nbsp;<b>•</b> ');

  const printWindow = window.open('', '_blank', 'width=900,height=800');
  if (!printWindow) {
    alert('Please allow popups to download or print your PDF Legal Memo.');
    return;
  }

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>NyayaPath Legal Guidance Memorandum — ${docId}</title>
        <style>
          @page {
            size: A4;
            margin: 20mm 15mm 20mm 15mm;
          }
          body {
            font-family: 'Georgia', 'Times New Roman', serif;
            color: #0f172a;
            background: #ffffff;
            margin: 0;
            padding: 24px;
          }
          .header-box {
            border-bottom: 3px double #0f172a;
            padding-bottom: 16px;
            margin-bottom: 20px;
            text-align: center;
          }
          .title {
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 4px;
          }
          .subtitle {
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .meta-table {
            width: 100%;
            margin-bottom: 20px;
            font-size: 12px;
            border-collapse: collapse;
          }
          .meta-table td {
            padding: 6px 10px;
            border: 1px solid #e2e8f0;
          }
          .disclaimer-box {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 12px;
            font-size: 11px;
            color: #475569;
            margin-bottom: 24px;
            border-radius: 4px;
            font-style: italic;
          }
          .content {
            font-size: 13px;
            line-height: 1.7;
          }
          .directory-box {
            margin-top: 35px;
            border-top: 2px solid #0f172a;
            padding-top: 14px;
            font-size: 11px;
          }
          .footer {
            margin-top: 30px;
            border-top: 1px solid #e2e8f0;
            padding-top: 10px;
            font-size: 10px;
            color: #94a3b8;
            text-align: center;
          }
        </style>
      </head>
      <body>
        <div class="header-box">
          <div class="title">NYAYAPATH — CITIZEN LEGAL GUIDANCE MEMORANDUM</div>
          <div class="subtitle">Ethical Procedural Guidance Under Indian Criminal Law</div>
        </div>

        <table class="meta-table">
          <tr>
            <td style="width: 25%; font-weight: bold; background: #f8fafc;">Document ID:</td>
            <td><strong>${docId}</strong></td>
          </tr>
          <tr>
            <td style="font-weight: bold; background: #f8fafc;">Date of Guidance:</td>
            <td>${dateStr}</td>
          </tr>
          <tr>
            <td style="font-weight: bold; background: #f8fafc;">Governing Regime:</td>
            <td><strong>${regimeLabel}</strong></td>
          </tr>
          <tr>
            <td style="font-weight: bold; background: #f8fafc;">Incident Date:</td>
            <td>${offenceDate || 'Not specified in query'}</td>
          </tr>
          <tr>
            <td style="font-weight: bold; background: #f8fafc;">FIR / Notice Date:</td>
            <td>${firDate || 'Not specified in query'}</td>
          </tr>
          <tr>
            <td style="font-weight: bold; background: #f8fafc;">Verification Engine:</td>
            <td>NyayaPath Hand-Verified Statutory Allowlist Gate (2,820 Bare Acts)</td>
          </tr>
        </table>

        <div class="disclaimer-box">
          <strong>MANDATORY STATUTORY NOTICE:</strong> This memorandum contains educational legal information synthesized by the NyayaPath reasoning agent. It is designed to assist citizens in understanding criminal offences, procedural rights, and statutory transitions under Indian law. This document does not constitute formal legal representation under the Advocates Act, 1961. Always consult an advocate enrolled with the State Bar Council before initiating judicial proceedings.
        </div>

        <div class="content">
          ${formattedHtml}
        </div>

        <div class="directory-box">
          <strong>FREE LEGAL AID & EMERGENCY HELPLINE DIRECTORY:</strong><br>
          • <strong>National Legal Services Authority (NALSA):</strong> Helpline 15100 (Toll-Free, 24x7)<br>
          • <strong>Police Emergency:</strong> 112 | <strong>Women Helpline:</strong> 181 | <strong>Mental Health (Tele-MANAS):</strong> 14416<br>
          • <strong>District Legal Services Authority (DLSA):</strong> Available at every District Court complex in India<br>
          • <strong>Official Portal:</strong> https://nalsa.gov.in | <strong>India Code:</strong> https://indiacode.nic.in
        </div>

        <div class="footer">
          NyayaPath Portfolio Project · Ethical AI Legal Guidance · End of Memorandum
        </div>

        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
            }, 300);
          }
        </script>
      </body>
    </html>
  `);
  printWindow.document.close();
}
