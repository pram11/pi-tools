use html2md::backend::comrak::ComrakBackend;
use html2md::backend::custom::CustomBackend;
use html2md::converter::Converter;

/// Verify both backends implement trait correctly.
mod comrak {
    use super::*;

    #[test]
    fn has_name() {
        let b = ComrakBackend;
        assert_eq!(b.name(), "comrak");
    }

    #[test]
    fn convert_returns_result() {
        let b = ComrakBackend;
        let _ = b.convert("<p>test</p>");
    }
}

mod custom {
    use super::*;

    #[test]
    fn has_name() {
        let b = CustomBackend;
        assert_eq!(b.name(), "custom");
    }

    #[test]
    fn convert_returns_result() {
        let b = CustomBackend;
        let _ = b.convert("<p>test</p>");
    }
}

/// Trait object dispatch works.
#[test]
fn trait_object_dispatch() {
    let backends: Vec<&dyn Converter> = vec![&ComrakBackend, &CustomBackend];
    for b in backends {
        assert!(!b.name().is_empty());
    }
}

/// Error variants exist and format.
mod errors {
    use html2md::converter::ConverterError;

    #[test]
    fn unknown_backend_formats() {
        let e = ConverterError::UnknownBackend("fake".into());
        assert!(e.to_string().contains("fake"));
    }

    #[test]
    fn sanitization_formats() {
        let e = ConverterError::Sanitization("broken".into());
        assert!(e.to_string().contains("broken"));
    }
}
