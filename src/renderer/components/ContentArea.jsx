import React from 'react';

export default function ContentArea({ showAgent, webviewRef, src }) {
  return (
    <div className="content-area">
      <div
        className="webview-container"
        style={{ width: showAgent ? '60%' : '100%' }}
      >
        <webview
          id="webview"
          ref={webviewRef}
          src={src}
          style={{ width: '100%', height: '100%', border: 'none', background: '#ffffff' }}
        />
      </div>

      {showAgent && (
        <div className="agent-panel">
          <div className="agent-header">Agent</div>
          <div className="agent-body">
            <p>Modo Agent ativo.</p>
            <p>Coloque aqui os componentes e interações do seu agente.</p>
          </div>
        </div>
      )}
    </div>
  );
}
