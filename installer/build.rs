fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows") {
        embed_resource::compile("installer.rc", embed_resource::NONE).manifest_required().expect("Windows icon resource compilation failed");
    }
}
