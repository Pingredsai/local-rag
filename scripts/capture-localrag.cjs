const fs = require("node:fs");
const path = require("node:path");

const projectRoot = path.resolve(__dirname, "..");
const outDir = path.join(projectRoot, "docs", "screenshots");
const videoDir = path.join(projectRoot, "demo", "video");
const demoFile = path.join(projectRoot, "demo", "nova-employee-handbook.md");
const playwrightModule = process.env.PLAYWRIGHT_PATH || "playwright";
const { chromium } = require(playwrightModule);

fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(videoDir, { recursive: true });

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function deleteAllDocuments() {
  const response = await fetch("http://localhost:8080/api/documents");
  const payload = await response.json();
  for (const doc of payload.documents || []) {
    await fetch(`http://localhost:8080/api/documents/${doc.document_id}`, { method: "DELETE" });
  }
}

async function waitForAssistantAnswer(page, minimumMessages) {
  await page.waitForFunction(
    (count) => {
      const messages = [...document.querySelectorAll(".msg.bot")];
      if (messages.length < count) return false;
      const last = messages[messages.length - 1];
      const text = last.querySelector(".bubble")?.textContent || "";
      return text && text !== "…" && !text.startsWith("❌") && last.querySelector(".sources");
    },
    minimumMessages,
    { timeout: 180000 }
  );
}

(async () => {
  await deleteAllDocuments();

  const channel = process.env.PLAYWRIGHT_CHANNEL;
  const browser = await chromium.launch({
    headless: true,
    ...(channel ? { channel } : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    recordVideo: {
      dir: videoDir,
      size: { width: 1440, height: 900 },
    },
  });
  const page = await context.newPage();

  try {
    await page.goto("http://localhost:8080", { waitUntil: "networkidle" });
    await page.waitForFunction(() => {
      const status = document.querySelector("#status")?.textContent || "";
      return status.includes("服务正常");
    });
    await sleep(900);
    await page.screenshot({ path: path.join(outDir, "01-home.png") });

    await page.setInputFiles("#fileInput", demoFile);
    await page.waitForFunction(() => document.querySelector("#docCount")?.textContent?.trim() === "1");
    await page.waitForFunction(() => {
      return [...document.querySelectorAll(".bubble")].some((el) => el.textContent.includes("已索引"));
    });
    await sleep(900);
    await page.screenshot({ path: path.join(outDir, "02-indexed.png") });

    await page.fill("#input", "星云科技正式员工每年有多少天年假？");
    await page.click("#sendBtn");
    await waitForAssistantAnswer(page, 1);
    await sleep(1200);
    await page.screenshot({ path: path.join(outDir, "03-answer-with-source.png") });

    await page.fill("#input", "内部文档可以上传到公有云 AI 吗？");
    await page.click("#sendBtn");
    await waitForAssistantAnswer(page, 2);
    await sleep(1200);
    await page.screenshot({ path: path.join(outDir, "04-policy-answer.png") });

    const video = page.video();
    await context.close();
    const recordedPath = await video.path();
    const videoPath = path.join(videoDir, "localrag-demo.webm");
    if (recordedPath !== videoPath) {
      fs.copyFileSync(recordedPath, videoPath);
    }
    await browser.close();

    console.log(JSON.stringify({
      screenshots: [
        path.join(outDir, "01-home.png"),
        path.join(outDir, "02-indexed.png"),
        path.join(outDir, "03-answer-with-source.png"),
        path.join(outDir, "04-policy-answer.png"),
      ],
      video: videoPath,
    }, null, 2));
  } catch (error) {
    await context.close();
    await browser.close();
    throw error;
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});