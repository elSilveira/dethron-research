use serde_json::json;
use tron_v2::{network::connector::Endpoint, neural::validation};

#[test]
fn local_and_ssh_endpoints_preserve_arguments_without_shell_injection() {
    let local = Endpoint::parse(&json!({"name":"cpu-1","kind":"local", "python":"C:/my python/python.exe", "model":"C:/my model", "device":"cpu"})).unwrap();
    let command = local.command();
    assert_eq!(command.get_program(), "C:/my python/python.exe");
    assert!(command.get_args().any(|a| a == "C:/my model"));
    let remote = Endpoint::parse(&json!({"name":"remote","kind":"ssh","host":"user@node",
        "python":"/env/python","model":"/models/a'b","directory":"/app dir","device":"cpu"}))
    .unwrap();
    let command = remote.command();
    let args: Vec<_> = command.get_args().map(|a| a.to_str().unwrap()).collect();
    assert!(args.contains(&"BatchMode=yes"));
    assert!(args.contains(&"StrictHostKeyChecking=yes"));
    assert!(args.last().unwrap().contains("'/models/a'\"'\"'b'"));
    for host in ["-oProxyCommand=bad", "host;bad", "host\nother"] {
        assert!(Endpoint::parse(&json!({"name":"r","kind":"ssh","host":host,
            "python":"python","model":"model","directory":"app","device":"cpu"}))
        .is_err());
    }
}

#[test]
fn ssh_identity_requires_a_real_model_but_not_a_local_parent_pid() {
    let file = json!({"sha256":"a".repeat(64),"bytes":1});
    let mut message = json!({"schema":1,"kind":"ready","pid":42,"parent_pid":41,
        "data":{"simulated":false,"load_count":1,"checkpoint":{"model_type":"qwen2",
        "files":{"config.json":file,"tokenizer.json":file,"tokenizer_config.json":file,"model.safetensors":file}}}});
    assert!(validation::ready(&message, 99).is_err());
    assert!(validation::ready_remote(&message).is_ok());
    message["data"]["simulated"] = json!(true);
    assert!(validation::ready_remote(&message).is_err());
    message["data"]["simulated"] = json!(false);
    message["pid"] = json!(0);
    assert!(validation::ready_remote(&message).is_err());
}
