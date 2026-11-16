import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App as AntApp, ConfigProvider } from "antd";
import ru from "antd/locale/ru_RU";
import dayjs from "dayjs";
import "dayjs/locale/ru";
import App from "./App";
import { AuthGate } from "./platform/AuthGate";
import "./styles.scss";
dayjs.locale("ru");
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={ru}
      theme={{
        token: {
          colorPrimary: "#22211d",
          colorInfo: "#22211d",
          colorBgLayout: "#f5f3ef",
          borderRadius: 10,
          fontFamily: "Inter, Arial, sans-serif",
        },
        components: {
          Button: { primaryShadow: "none" },
          Layout: { bodyBg: "#f5f3ef" },
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <AuthGate>
            <App />
          </AuthGate>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>,
);

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .catch((error) =>
        console.error("Service worker registration failed", error),
      );
  });
}
