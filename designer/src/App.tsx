import { Routes, Route, Link } from "react-router-dom";
import SchemaList from "./pages/SchemaList";
import SchemaEditor from "./pages/SchemaEditor";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">
          問卷設計工作室
        </Link>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<SchemaList />} />
          <Route path="/schemas/:id" element={<SchemaEditor />} />
        </Routes>
      </main>
    </div>
  );
}
