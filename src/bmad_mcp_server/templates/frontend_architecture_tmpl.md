# Frontend Architecture: {{ project_name }}

## 1. Frontend Technical Summary
   - **Overview:** {{ frontend_overview }}
   - **Alignment with Main Architecture:** {{ alignment_summary }}
   - **Key Frontend Decisions:** {{ key_frontend_decisions }}
   - **Goals:** {{ frontend_architectural_goals }}

## 2. Framework and Core Libraries Selection
   - **Primary Framework:** {{ frontend_framework }} (Version: {{ frontend_framework_version }})
     - Justification: {{ framework_justification }}
   - **UI Component Library:** {{ ui_component_library }} (Version: {{ ui_library_version }})
     - Justification: {{ ui_library_justification }}
   - **State Management:** {{ state_management_library }} (Version: {{ state_management_version }})
     - Justification: {{ state_management_justification }}
   - **Routing:** {{ routing_library }} (Version: {{ routing_version }})
     - Justification: {{ routing_justification }}
   - **API Client:** {{ api_client_library }} (e.g., Axios, Fetch API)
   - **Utility Libraries:** {{ utility_libraries }} (e.g., Lodash, Date-fns)

## 3. Component Architecture Strategy
   - **Design Pattern:** {{ component_pattern }} (e.g., Atomic Design, Feature-Sliced Design)
     - Justification: {{ component_pattern_justification }}
   - **Directory Structure for Components:**
     ```
     src/
     ├── components/
     │   ├── atoms/
     │   ├── molecules/
     │   ├── organisms/
     │   ├── templates/
     │   └── pages/ (or features/)
     └── ...
     ```
   - **Component Naming Conventions:** {{ component_naming_conventions }}
   - **Props and State Management within Components:** {{ component_props_state_strategy }}
   - **Reusability Guidelines:** {{ component_reusability_guidelines }}

## 4. State Management Approach
   - **Global State Strategy:** {{ global_state_strategy }}
   - **Local Component State Strategy:** {{ local_state_strategy }}
   - **Data Flow:** {{ data_flow_description }} (e.g., Unidirectional, Flux)
   - **Async Operations Handling:** {{ async_operations_handling }} (e.g., Thunks, Sagas, Observables)

## 5. Routing and Navigation Design
   - **Routing Strategy:** {{ routing_strategy }} (e.g., Client-side, Server-side)
   - **Route Definitions:** {{ route_definitions_example }}
   - **Lazy Loading of Routes/Components:** {{ lazy_loading_strategy }}
   - **Navigation Guards/Middleware:** {{ navigation_guards_strategy }}

## 6. Build and Bundling Configuration
   - **Build Tool:** {{ build_tool }} (e.g., Webpack, Vite, Parcel)
   - **Key Build Optimizations:** {{ build_optimizations }} (e.g., Code Splitting, Tree Shaking)
   - **Environment Configuration:** {{ environment_config_strategy }} (dev, staging, prod)
   - **Asset Management:** {{ asset_management_strategy }} (images, fonts, etc.)

## 7. Performance Optimization Strategy
   - **Key Performance Metrics (KPIs):** {{ performance_kpis }} (e.g., LCP, FID, CLS)
   - **Optimization Techniques:** {{ optimization_techniques }} (e.g., Memoization, Virtualization, Debouncing)
   - **Image Optimization:** {{ image_optimization_strategy }}
   - **Caching Strategy:** {{ frontend_caching_strategy }}

## 8. Accessibility (a11y) and Internationalization (i18n)
   - **Accessibility Standards:** {{ accessibility_standards }} (e.g., WCAG 2.1 AA)
   - **ARIA Attributes Usage:** {{ aria_usage_guidelines }}
   - **Keyboard Navigation:** {{ keyboard_navigation_plan }}
   - **Internationalization Strategy:** {{ i18n_strategy }}
   - **Localization (l10n) Approach:** {{ l10n_approach }}

## 9. Testing Strategy
   - **Unit Tests:** Framework: {{ unit_test_framework }}, Coverage Target: {{ unit_test_coverage }}%
   - **Component Tests:** Framework: {{ component_test_framework }}
   - **Integration Tests:** {{ integration_test_strategy }}
   - **End-to-End (E2E) Tests:** Framework: {{ e2e_test_framework }}
   - **Visual Regression Testing:** {{ visual_regression_tool }}
   - **Mocking Strategy:** {{ mocking_strategy }}

## 10. Development Workflow and Standards
   - **Branching Strategy:** {{ branching_strategy }} (e.g., GitFlow)
   - **Code Review Process:** {{ code_review_process }}
   - **Linters and Formatters:** {{ linters_formatters }} (e.g., ESLint, Prettier)
   - **Commit Message Conventions:** {{ commit_message_conventions }}
   - **IDE Setup and Extensions:** {{ ide_setup_recommendations }}

## 11. Deployment and CI/CD Pipeline
   - **CI/CD Platform:** {{ ci_cd_platform }}
   - **Build Steps:** {{ ci_build_steps }}
   - **Testing Steps:** {{ ci_testing_steps }}
   - **Deployment Steps:** {{ ci_deployment_steps }}
   - **Rollback Strategy:** {{ frontend_rollback_strategy }}

## 12. Security Considerations
   - **Cross-Site Scripting (XSS) Prevention:** {{ xss_prevention_measures }}
   - **Cross-Site Request Forgery (CSRF) Prevention:** {{ csrf_prevention_measures }}
   - **Content Security Policy (CSP):** {{ csp_implementation_plan }}
   - **Secure API Communication:** {{ secure_api_communication_details }} (HTTPS, token handling)
   - **Dependency Vulnerability Scanning:** {{ dependency_scanning_tool }}

## 13. Error Handling and Monitoring
   - **Client-Side Error Logging:** {{ client_error_logging_tool }}
   - **Performance Monitoring:** {{ client_performance_monitoring_tool }}
   - **User Feedback Mechanisms for Errors:** {{ error_feedback_mechanism }}

## 14. Implementation Guidance for AI Agents
   - **Key files/directories for AI focus:** {{ key_frontend_files_for_ai }}
   - **Component generation patterns for AI:** {{ component_generation_patterns_for_ai }}
   - **State management interaction for AI:** {{ state_management_interaction_for_ai }}
   - **Testing script generation for AI:** {{ testing_script_generation_for_ai }}

---
*Generated by BMAD MCP Server*
