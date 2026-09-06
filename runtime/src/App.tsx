import { Routes, Route } from "react-router-dom";
import FillPage from "./pages/FillPage";
import SuccessPage from "./pages/SuccessPage";

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/f/:slug" element={<FillPage mode="public" />} />
        <Route path="/preview/:token" element={<FillPage mode="preview" />} />
        <Route path="/done" element={<SuccessPage />} />
        <Route
          path="*"
          element={
            <main className="main">
              <div className="card">
                <h1>問卷填寫</h1>
                <p className="muted">請使用 /f/:slug 或 /preview/:token 進入</p>
              </div>
            </main>
          }
        />
      </Routes>
    </div>
  );
}
