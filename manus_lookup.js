/**
 * Nginx njs module for dynamic port lookup
 * Reads /tmp/manus_port_mappings.json to route subdomain.manus.you -> localhost:port
 */

function get_port(r) {
    try {
        var fs = require('fs');
        var mappingFile = '/tmp/manus_port_mappings.json';

        // Read mapping file
        var data = fs.readFileSync(mappingFile);
        var mappings = JSON.parse(data);

        // Extract subdomain from Host header
        // Format: abc123.manus.you -> abc123
        var host = r.headersIn.Host;
        var subdomain = host.split('.')[0];

        // Lookup port for this subdomain
        if (mappings[subdomain]) {
            var port = mappings[subdomain].port;
            r.log('[manus_lookup] ' + subdomain + ' -> port ' + port);
            return port.toString();
        }

        r.log('[manus_lookup] Subdomain not found: ' + subdomain);
        return "";

    } catch (e) {
        r.error('[manus_lookup] Error: ' + e.toString());
        return "";
    }
}

export default {get_port};
